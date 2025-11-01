import asyncio

from app.api.details_controller import breakdown

async def main():
    area = "BUKIT BATOK CENTRAL"
    res = await breakdown(area)
    print("Result type:", type(res))
    try:
        print("Scores:", res.scores)
    except Exception as e:
        print("Error accessing scores:", e)

if __name__ == "__main__":
    asyncio.run(main())
