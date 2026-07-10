from fastapi import APIRouter


router = APIRouter()


@router.post("/login")
async def login() -> dict[str, str]:
    raise NotImplementedError("Login is not implemented yet.")


@router.post("/signup")
async def signup() -> dict[str, str]:
    raise NotImplementedError("Signup is not implemented yet.")

