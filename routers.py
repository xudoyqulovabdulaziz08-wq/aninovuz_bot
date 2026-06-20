from aiogram import Router

from handlers import(
    start,
    search,
    qollanma,
    reklama
)






main_router = Router()



main_router.include_routers(

    start.router,
    qollanma.router,
    reklama.router,


    search.router

)