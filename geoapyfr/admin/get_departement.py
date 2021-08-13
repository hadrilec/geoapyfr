# -*- coding: utf-8 -*-

import pandas as pd
from shapely.ops import cascaded_union

from .get_commune import get_commune
from ._get_departement_list import _get_departement_list

def get_departement(region=None, geometry=False, geo='france-zoom-overseas-paris'):
    
    deps = _get_departement_list(region=region)
    deps.columns = list_col = ['departement_nom', 'departement_code', 'region_code']
    
    if geometry is True:
        communes = get_commune(region=region,
                               geometry=geometry,
                               geo=geo)
        
        dep_list = communes.departement_code.unique()
        
        list_dep_with_geom = []
        
        for d in dep_list:
            df = communes[communes['departement_code'] == d]
            polygons = df['geometry'].to_list()
            df = df[list_col].drop_duplicates()
            df['geometry'] =  [cascaded_union(polygons)]
            list_dep_with_geom.append(df)
        
        deps = pd.concat(list_dep_with_geom)   
        
    deps = deps.reset_index(drop=True)
    
    return(deps)
