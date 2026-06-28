
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timezone, timedelta
from sqlalchemy import case, select, update
from sqlalchemy.dialects.postgresql import insert

from database.models import DBUser, UserStatus

logger = logging.getLogger("DataRepository")







class DataRepository:
    # ================= SESSION HELPERS =================
    @staticmethod
    def _get_real_session(session: Any):
        if hasattr(session, "_session"):
            return session._session
        return session

    @staticmethod
    async def _prepare_session(session: Any):
        if hasattr(session, "_ensure_session"):
            await session._ensure_session()
        return DataRepository._get_real_session(session)

# ================= GET DATABASE SIZE =================
    @staticmethod
    async def get_db_size(session: Any) -> str:
        from sqlalchemy import text
        session = await DataRepository._prepare_session(session)
        
        try:
            # Joriy ulangan bazaning nomini va uning diskdagi hajmini aniqlaymiz
            # pg_size_pretty funksiyasi avtomatik '45 MB' yoki '1.2 GB' formatiga o'tkazib beradi
            stmt = text("SELECT pg_size_pretty(pg_database_size(current_database()));")
            result = await session.execute(stmt)
            return result.scalar() or "0 MB"
        except Exception as e:
            logger.error(f"❌ Baza hajmini hisoblashda xatolik: {e}")
            return "Noma'lum"
        
    
    # ================= CLEAR PROCESSED OUTBOX EVENTS =================
    @staticmethod
    async def clear_processed_outbox(session: Any) -> int:
        from sqlalchemy import delete
        from database.models import OutboxEvent
        
        session = await DataRepository._prepare_session(session)

        # Faqat processed=True bo'lgan, ya'ni vazifasini bajarib bo'lgan loglarni o'chiramiz
        stmt = delete(OutboxEvent).where(OutboxEvent.processed == True)
        result = await session.execute(stmt)
        
        await session.flush()
        return result.rowcount  # Qancha qator o'chirilganini qaytaradi
    

    
    # ================= GENERATE SQL BACKUP DUMP (FIXED PRO) =================
    @staticmethod
    async def generate_sql_dump(session: Any) -> str:
        from sqlalchemy import select
        from datetime import datetime
        # Barcha modellarni aniq import qilamiz
        from database.models import DBUser, Anime, Episode, Genre, Channel, anime_genres
        
        session = await DataRepository._prepare_session(session)
        sql_lines = [
            "-- 📥 ANI-NOVUZ TELEGRAM BOT DATABASE BACKUP DUMP\n",
            f"-- Generatsiya vaqti: {datetime.now().isoformat()}\n",
            "SET statement_timeout = 0;\n",
            "SET lock_timeout = 0;\n",
            "SET client_encoding = 'UTF-8';\n\n"
        ]

        try:
            # 1. USERS JADVALINI EKSPORT QILISH
            users_res = await session.execute(select(DBUser))
            for u in users_res.scalars().all():
                username = f"'{u.username.replace("'", "''")}'" if u.username else "NULL"
                vip_date = f"'{u.vip_expire_date.isoformat()}'" if u.vip_expire_date else "NULL"
                joined = f"'{u.joined_at.isoformat()}'" if u.joined_at else "NOW()"
                sql_lines.append(
                    f"INSERT INTO users (user_id, username, joined_at, points, status, vip_expire_date, sleep_reminder_enabled) "
                    f"VALUES ({u.user_id}, {username}, {joined}, {u.points}, '{u.status.value}', {vip_date}, {str(u.sleep_reminder_enabled).lower()}) "
                    f"ON CONFLICT (user_id) DO UPDATE SET username=EXCLUDED.username, status=EXCLUDED.status, points=EXCLUDED.points, vip_expire_date=EXCLUDED.vip_expire_date;\n"
                )
            sql_lines.append("\n")

            # 2. GENRES JADVALINI EKSPORT QILISH
            genres_res = await session.execute(select(Genre))
            for g in genres_res.scalars().all():
                g_name = g.name.replace("'", "''")
                sql_lines.append(
                    f"INSERT INTO genres (id, name) VALUES ({g.id}, '{g_name}') "
                    f"ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name;\n"
                )
            sql_lines.append("\n")

            # 3. ANIME_LIST JADVALINI EKSPORT QILISH
            anime_res = await session.execute(select(Anime))
            for a in anime_res.scalars().all():
                title = a.title.replace("'", "''")
                poster = f"'{a.poster_id.replace("'", "''")}'" if a.poster_id else "NULL"
                year_val = a.year if a.year else "NULL"
                
                # Description ichidagi har qanday slesh va tirnoqlarni SQL xavfsiz holatga keltiramiz
                clean_desc = f"'{a.description.replace("'", "''")}'" if a.description else "NULL"
                
                # PostgreSQL Array formatini to'g'ri o'girish
                if a.languages:
                    lang_array = "ARRAY[" + ", ".join([f"'{l.replace("'", "''")}'" for l in a.languages]) + "]::varchar[]"
                else:
                    lang_array = "ARRAY[]::varchar[]"

                sql_lines.append(
                    f"INSERT INTO anime_list (anime_id, title, poster_id, year, description, languages, rating_sum, rating_count, views_week, is_completed) "
                    f"VALUES ({a.anime_id}, '{title}', {poster}, {year_val}, {clean_desc}, {lang_array}, {a.rating_sum}, {a.rating_count}, {a.views_week}, {str(a.is_completed).lower()}) "
                    f"ON CONFLICT (anime_id) DO UPDATE SET title=EXCLUDED.title, poster_id=EXCLUDED.poster_id, year=EXCLUDED.year, description=EXCLUDED.description, languages=EXCLUDED.languages, is_completed=EXCLUDED.is_completed;\n"
                )
            sql_lines.append("\n")

            # 4. ANIME_GENRES (MANY-TO-MANY RELATIONSHIP) EKSPORT QILISH
            genres_m2m = await session.execute(select(anime_genres))
            for row in genres_m2m.all():
                sql_lines.append(
                    f"INSERT INTO anime_genres (anime_id, genre_id) VALUES ({row.anime_id}, {row.genre_id}) "
                    f"ON CONFLICT (anime_id, genre_id) DO NOTHING;\n"
                )
            sql_lines.append("\n")

            # 5. ANIME_EPISODES JADVALINI EKSPORT QILISH
            episode_res = await session.execute(select(Episode))
            for ep in episode_res.scalars().all():
                sql_lines.append(
                    f"INSERT INTO anime_episodes (id, anime_id, episode, file_id) "
                    f"VALUES ({ep.id}, {ep.anime_id}, {ep.episode}, '{ep.file_id}') "
                    f"ON CONFLICT (anime_id, episode) DO UPDATE SET file_id=EXCLUDED.file_id;\n"
                )
            sql_lines.append("\n")

            # 6. CHANNELS JADVALINI EKSPORT QILISH
            channels_res = await session.execute(select(Channel))
            for ch in channels_res.scalars().all():
                ch_title = ch.title.replace("'", "''")
                url_val = f"'{ch.url.replace("'", "''")}'" if ch.url else "NULL"
                sql_lines.append(
                    f"INSERT INTO channels (id, channel_id, title, url, is_active, created_at) "
                    f"VALUES ({ch.id}, {ch.channel_id}, '{ch_title}', {url_val}, {str(ch.is_active).lower()}, '{ch.created_at.isoformat()}') "
                    f"ON CONFLICT (channel_id) DO UPDATE SET title=EXCLUDED.title, url=EXCLUDED.url, is_active=EXCLUDED.is_active;\n"
                )

            return "".join(sql_lines)
            
        except Exception as e:
            logger.error(f"❌ Professional SQL Dump yaratishda jiddiy xatolik: {e}")
            return f"-- Export error: {str(e)}"
        


    # ================= SAFE EXECUTE SQL SCRIPT (IMPORT) =================
    @staticmethod
    async def execute_sql_backup(session: Any, sql_content: str) -> bool:
        from sqlalchemy import text
        session = await DataRepository._prepare_session(session)
        
        try:
            # SQL tarkibidagi barcha buyruqlarni bitta tranzaksiya ichida ijro etamiz
            await session.execute(text(sql_content))
            await session.flush()
            return True
        except Exception as e:
            logger.error(f"❌ SQL dump ijro etishda (Import) jiddiy xatolik: {e}")
            return False