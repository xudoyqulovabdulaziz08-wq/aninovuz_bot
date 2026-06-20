from aiogram import Router

from handlers import(
    start,
    search
)






main_router = Router()



main_router.include_routers(

    start.router,



    search.router

)