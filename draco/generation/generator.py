import random
from copy import deepcopy
from typing import Any, Dict, List, Set, Union

from draco.generation.helper import is_valid
from draco.generation.model import Model
from draco.generation.spec import Spec
from draco.spec import Data, Field, Query, Task


class Generator:
    """
    A Generator can be used to generate specs that represent
    mutations over a list of properties.
    """
    def __init__(self, distributions: Dict, type_distribution: Dict,
                       definitions: Dict, data_schema: Dict, data_url: str) -> None:
        top_level_props = definitions['topLevelProps']
        encoding_props = definitions['encodingProps']
        data_fields = [Field(x['name'], x['type'], cardinality=x['cardinality']) for x in data_schema]

        self.model = Model(data_fields, distributions, type_distribution, top_level_props, encoding_props)
        self.data = Data(data_fields)
        self.data_url = data_url

    def generate_cross_interaction(self, props: List[str], dimensions: int,
                seen_base_specs: Set[Spec]) -> List[Spec]:
        """
        Generates a list of specs by enumerating over the given properties' enums.
        """
        base_spec = self.model.generate_spec(dimensions)
        self.model.pre_improve(base_spec, props)

        while (base_spec in seen_base_specs):
            base_spec = self.model.generate_spec(dimensions)
            self.model.pre_improve(base_spec, props)

        seen_base_specs.add(base_spec)

        specs: List[Spec] = []
        self.__mutate_spec_cross(base_spec, props, 0, set(), specs)

        return specs

    def __mutate_spec_no_cross(self, base_spec: Spec, props: List[str], prop_index: int,
                            seen: Set[Spec], groups: List[List[Spec]]):
        # base case
        if (prop_index == len(props)):
            self.model.post_improve(base_spec, props)

            # within a group, don't repeat the same specs
            if not (base_spec in seen):
                seen.add(base_spec)

                query = Query.from_vegalite(base_spec)

                if (is_valid(Task(self.data, query))):
                    base_spec['data'] = { 'url': self.data_url }
                    groups[-1].append(base_spec)
        else:
            if (prop_index == len(props) - 1):
                groups.append([])

            prop_to_mutate = props[prop_index]
            for enum in self.model.get_enums(prop_to_mutate):
                spec = deepcopy(base_spec)
                self.model.mutate_prop_cross(spec, prop_to_mutate, enum)

                # recursive call
                self.__mutate_spec_cross(spec, props, prop_index + 1, seen, groups)

        return


    def __mutate_spec_cross(self, base_spec: Spec, props: List[str], prop_index: int,
                            seen: Set[Spec], specs: List[Spec]):
        # base case
        if (prop_index == len(props)):
            self.model.post_improve(base_spec, props)

            # within a group, don't repeat the same specs
            if not (base_spec in seen):
                seen.add(base_spec)

                query = Query.from_vegalite(base_spec)

                if (is_valid(Task(self.data, query))):
                    base_spec['data'] = { 'url': self.data_url }
                    specs.append(base_spec)
         # recursive case
        else:
            prop_to_mutate = props[prop_index]
            for enum in self.model.get_enums(prop_to_mutate):
                spec = deepcopy(base_spec)
                self.model.mutate_prop_cross(spec, prop_to_mutate, enum)

                # recursive call
                self.__mutate_spec_cross(spec, props, prop_index + 1, seen, specs)

        return
