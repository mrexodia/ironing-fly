def main():
    import argparse
    import uvicorn
    parser = argparse.ArgumentParser(description='Run the Ironing Fly simulation API')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run('ironing_fly.server:app', host='127.0.0.1', port=args.port)


if __name__ == "__main__":
    main()
