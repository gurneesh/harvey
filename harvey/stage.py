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
            image_output = f'Test image created\n{image[1]}'
            print(image_output)
        except:
            # TODO: Does not catch if image isn't built
            sys.exit('Error: Harvey could not build image')

        # Create a container
        try:
            container = Container.create(image[0])
            container_output = 'Test container created'
            print(container_output)
        except:
            # TODO: Does not catch if image does not exist
            sys.exit("Error: Harvey could not create container")

        # Start the container
        try:
            Container.start(container['Id'])
            start_output = 'Test container started'
            print(start_output)
        except:
            sys.exit("Error: Harvey could not start container")

        # Wait for container to exit
        try:
            Container.wait(container['Id'])
            wait_output = 'Waiting for Test container to exit'
            print(wait_output)
        except:
            sys.exit("Error: Harvey could not wait for container")

        # Return logs
        try:
            logs = Container.logs(container['Id'])
            logs_output = '\nTest logs:\n============================================================\n\n' \
                + logs + '============================================================\n'
            print(logs_output)
        except:
            sys.exit("Error: Harvey could not create container logs")

        # Remove container and image after it's done
        try:
            Container.remove(container['Id'])
            Image.remove(image)
            remove_output = 'Test container and image removed'
            print(remove_output)
        except:
            sys.exit("Error: Harvey could not remove container and/or image")

        execution_time = f'Test stage execution time: {datetime.now() - start_time}'
        print(execution_time)

        test = f'{image_output}\n{container_output}\n{start_output}\n{wait_output}\n\
            {logs_output}\n{remove_output}\n{execution_time}\n'
        print(test)

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
            image_output = f'Project image created\n{image[1]}'
            print(image_output)
        except:
            sys.exit("Error: Harvey could not finish the build stage")

        execution_time = f'Build stage execution time: {datetime.now() - start_time}'
        print(execution_time)

        build = f'{image_output}\n{execution_time}\n'
        return build

    @classmethod
    def deploy(cls, webhook):
        """Deploy Stage"""
        start_time = datetime.now()
        repo_name = webhook["repository"]["name"].lower()
        owner_name = webhook["repository"]["owner"]["name"].lower()
        # Tear down the old container if one exists
        # TODO: Verify this logic actually works as intended
        try:
            resp = requests.get(Global.BASE_URL + f'containers/{owner_name}-{repo_name}/json')
            resp.raise_for_status()
            try:
                Container.stop(f'{owner_name}-{repo_name}')
                stop_output = 'Old project container stopping'
                print(stop_output)
                Container.wait(f'{owner_name}-{repo_name}')
                wait_output = 'Old project container waiting to exit'
                print(wait_output)
                Container.remove(f'{owner_name}-{repo_name}')
                remove_output = 'Old project container removed'
                print(remove_output)
            except:
                sys.exit("Error: Harvey failed during old/new container swap")
        except requests.exceptions.HTTPError as err:
            print(err)
            stop_output = ''
            wait_output = ''
            remove_output = ''

        # Create a container
        try:
            container = Container.create(f'{owner_name}-{repo_name}')
            create_output = 'Project container created'
            print(create_output)
        except:
            sys.exit("Error: Harvey could not create the container in the deploy stage")

        # Start the container
        try:
            Container.start(container['Id'])
            start_output = 'Project container started'
            print(start_output)
        except:
            sys.exit("Error: Harvey could not start the container in the deploy stage")

        execution_time = f'Deploy stage execution time: {datetime.now() - start_time}'
        print(execution_time)

        deploy = f'{stop_output}\n{wait_output}\n{remove_output}\n{create_output}\n{start_output}\n{execution_time}\n'
        return deploy

    @classmethod
    def build_deploy_compose(cls, config, webhook):
        """Build Stage - USING A DOCKER COMPOSE FILE"""
        start_time = datetime.now()
        full_name = webhook["repository"]["full_name"].lower()
        if "compose" in config:
            compose = f'-f {config["compose"]}'
        else:
            compose = ''

        # Build the image and container from the docker-compose file
        try:
            compose = os.popen(f'cd {Global.PROJECTS_PATH}{full_name} && docker-compose {compose} up -d --build')
            compose_output = f'{compose.read()}'
            print(compose_output)
        except:
            sys.exit("Error: Harvey could not finish the build/deploy compose stage")

        execution_time = f'Build/Deploy stage execution time: {datetime.now() - start_time}'
        print(execution_time)

        deploy = f'{compose_output}\n{execution_time}\n'
        return deploy
