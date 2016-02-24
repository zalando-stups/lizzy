from typing import Optional, List  # NOQA
import pystache
import yaml


class SenzaDefinition:
    """
    Model a Simple Senza Definition
    See http://stups.readthedocs.org/en/latest/components/senza.html#senza-definition
    """

    def __init__(self, definition_yaml: str, arguments: List[str]):
        # TODO support named parameters
        # TODO: error handling
        self.definition = yaml.load(definition_yaml)
        senza_info = self.definition.get('SenzaInfo', {})  # type: dict
        senza_paramaters = senza_info.get('Parameters', [])  # type: List[Dict[str, Dict[str, str]]]
        keys = []
        arguments_map = {}
        for parameter in senza_paramaters:
            name = list(parameter.keys()).pop()
            keys.append(name)
            if 'Default' in parameter[name]:
                # Add the defaults to the parameter map
                arguments_map[name] = parameter[name]['Default']

        arguments_map.update(dict(zip(keys, arguments)))  # add provided values

        render = pystache.Renderer(missing_tags='strict')
        final_definition = render.render(definition_yaml, {'Arguments': arguments_map})
        self.definition = yaml.load(final_definition)

    @property
    def app_server(self) -> dict:
        for component in self.senza_components:
            if 'AppServer' in component:
                return component['AppServer']
        else:
            return {}

    @property
    def environment(self) -> dict:
        return self.app_server['TaupageConfig']['environment']

    @environment.setter
    def environment(self, value: dict):
        self.app_server['TaupageConfig']['environment'] = value

    @property
    def senza_components(self) -> list:
        return self.definition.get('SenzaComponents', [])

    @property
    def stack_name(self) -> str:
        return self.definition['SenzaInfo']['StackName']
