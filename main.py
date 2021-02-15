import yaml

from transfer.route import process_route

ROUTES_FILE = '/home/wspek/dev/investing/routes.yaml'


def main():
    with open(ROUTES_FILE) as routes_file:
        try:
            route_config = yaml.safe_load(routes_file)
        except yaml.YAMLError as e:
            print(e)

    for route in route_config:
        result = process_route(**route)
        print(result)
        print('------')


if __name__ == '__main__':
    main()
