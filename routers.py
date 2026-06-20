from aiogram import Router

from handlers import(
    start,
    search,
    qollanma,
    reklama,
    buy_vip,
    help
)






main_router = Router()



main_router.include_routers(

    start.router,
    qollanma.router,
    reklama.router,
    buy_vip.router,
    help.router,


    search.router

)