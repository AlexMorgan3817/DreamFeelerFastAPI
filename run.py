import uvicorn
import argparse

args = argparse.ArgumentParser()
args.add_argument("--debug", action="store_true")


if __name__ == "__main__":
    args = args.parse_args()
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=args.debug)
