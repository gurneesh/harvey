"""Import stage modules"""
# pylint: disable=W0511
import sys
import os
from datetime import datetime
import requests
import requests_unixsocket
from .globals import Global
from .container import Container
from .image import Image

requests_unixsocket.monkeypatch() # allows us to use requests_unixsocker via requests

class Stage(Global):
    """Stage methods"""
    @classmethod
    def test(cls, config, webhook):
        """Test Stage"""
        start_time = datetime.now()
        context = 'test'

        # Build the image
        try:
            image = Image.build(config, webhook, context)
            print(image, "\nImage created")
        except:
            # TODO: Does not catch if image isn't built
            sys.exit('Error: Harvey could not build image')

        # Create a container
        try:
            container = Container.create(image)
            print(container, "\nContainer created")
        except:
            # TODO: Does not catch if image does not exist
            sys.exit("Error: Harvey could not create container")

        # Start the container
        try:
            start = Container.start(container['Id'])
            print(start, "\nContainer started")
        except:
            sys.exit("Error: Harvey could not start container")

        # Wait for container to exit
        try:
            Container.wait(container['Id'])
        except:
            sys.exit("Error: Harvey could not wait for container")

        # Return logs
        try:
            logs = Container.logs(container['Id'])
            print("Logs created")
        except:
            sys.exit("Error: Harvey could not create container logs")

        # Remove container and image after it's done
        try:
            Container.remove(container['Id'])
            Image.remove(image)
            print("Container and image removed")
        except:
            print("Error: Harvey could not remove container and/or image")

        test = image + logs
        print(f'Test stage execution time: {datetime.now() - start_time}')
        return test

    @classmethod
    def build(cls, config, webhook):
        """Build Stage"""
        start_time = datetime.now()
        repo_name = webhook["repository"]["name"].lower()
        owner_name = webhook["repository"]["owner"]["name"].lower()
        # Build the image
        try:
            Image.remove(f'{owner_name}-{repo_name}')
            image = Image.build(config, webhook)
            print(image, "\nImage created")
        except:
            sys.exit("Error: Harvey could not finish the build stage")

        print(f'Build stage execution time: {datetime.now() - start_time}')
        return image

    @classmethod
    def deploy(cls, webhook):
        """Deploy Stage"""
        start_time = datetime.now()
        repo_name = webhook["repository"]["name"].lower()
        owner_name = webhook["repository"]["owner"]["name"].lower()
        # Tear down the old container if one exists
        try:
            resp = requests.get(Global.BASE_URL + f'containers/{owner_name}-{repo_name}/json')
            resp.raise_for_status()
            try:
                Container.stop(f'{owner_name}-{repo_name}')
                print("Container stopping")
                Container.wait(f'{owner_name}-{repo_name}')
                print("Container waiting")
                remove = Container.remove(f'{owner_name}-{repo_name}')
                print(remove, "\nOld container removed")
            except:
                sys.exit("Error: Harvey failed during old/new container swap")
        except requests.exceptions.HTTPError as err:
            print(err)

        # Create a container
        try:
            container = Container.create(f'{owner_name}-{repo_name}')
            print(container, "\nContainer created")
        except:
            sys.exit("Error: Harvey could not create the container in the deploy stage")

        # Start the container
        try:
            start = Container.start(container['Id'])
            print(start, "\nContainer started")
        except:
            sys.exit("Error: Harvey could not start the container in the deploy stage")

        print(f'Deploy stage execution time: {datetime.now() - start_time}')
        return start

    @classmethod
    def build_deploy_compose(cls, config, webhook):
        """Build Stage - USING A DOCKER COMPOSE FILE"""
        start_time = datetime.now()
        full_name = webhook["repository"]["full_name"].lower()
        context = f'/projects/{full_name}'
        if "compose" in config:
            compose = f'-f {config["compose"]}'
        else:
            compose = ''

        # Build the image and container from the docker-compose file
        try:
            compose = os.popen(f'cd {Global.TEST_PATH}{context} && docker-compose {compose} up -d --build')
            output = compose.read()
            print("Docker compose successful")
        except:
            sys.exit("Error: Harvey could not finish the build/deploy compose stage")

        print(f'Build/Deploy stage execution time: {datetime.now() - start_time}')
        return output
