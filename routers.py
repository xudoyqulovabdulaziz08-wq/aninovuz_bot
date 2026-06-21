from aiogram import Router

from handlers import(
    start,
    search,
    qollanma,
    reklama,
    buy_vip,
    help,
    admin_menu,
    creator_menu
)
from handlers.admin_panel.admin_anime import(
    anime_menu
)
from handlers.admin_panel.admin_channel import(
    channel_menu
)
from handlers.admin_panel.admin_advert import(
    admin_advet_menu
)




main_router = Router()



main_router.include_routers(

    start.router,
    creator_menu.router,

    admin_menu.router,

    anime_menu.router,
    channel_menu.router,
    admin_advet_menu.router,

    qollanma.router,
    reklama.router,
    buy_vip.router,
    help.router,


    search.router

)