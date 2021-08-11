# -*- coding: utf-8 -*-

import os
import appdirs
import pandas as pd
from tqdm import trange
from shapely.affinity import translate

from ._get_commune_from_departement import _get_commune_from_departement
from ._rescale_geom import _rescale_geom
from ._get_departement_list import _get_departement_list
from ._get_region_list import _get_region_list

def get_commune(region=None, departement=None, update=False,
                geometry=False, geo = 'france-zoom-overseas-paris'):
    
    list_geo = [ 
        'france-all',
        'france-metropolitan', 
        'france-zoom-overseas',
        'france-zoom-paris', 
        'france-zoom-overseas-paris'] 
    
    if geo not in list_geo:
        raise ValueError('!!! geo should be in : {} !!!'.format(' '.join(list_geo)))
    
    local_appdata_folder = appdirs.user_cache_dir()
    geoapyfr_folder = local_appdata_folder + '/geoapyfr'

    # create  folder
    if not os.path.exists(geoapyfr_folder):
        os.mkdir(geoapyfr_folder)
        
    link_file = geoapyfr_folder + '/communes'
    
    if (not os.path.exists(link_file)) | (update):
        
        reg = _get_region_list()
        
        reg_list = reg.region_code.to_list()
        
        if region is not None:
            reg_list = [reg for reg in reg_list if reg in region]
        
        deps = _get_departement_list(region=reg_list)
        
        deps_list = deps.code.to_list()
        
        if departement is not None:
            deps_list = [dep for dep in deps_list if dep in departement]
         
        coms = []
        
        for j in trange(len(deps_list)):
            
            df = _get_commune_from_departement(d=deps_list[j],
                                               update=update,
                                               geometry=geometry)       
                    
            coms.append(df)
        
        communes = pd.concat(coms).reset_index(drop=True)
        if region is None:
            if departement is None:
                communes.to_pickle(link_file)
    else:
        try:
            communes = pd.read_pickle(link_file)
        except:
            os.remove(link_file)
            communes = get_commune(region=region,
                                   departement=departement,
                                   update=True)
            
    #
    # Translate and zoom on overseas departements and Paris
    #
    
    list_ovdep = ['971', '972', '973', '974', '976']
    fm = communes[~communes['departement_code'].isin(list_ovdep)]
    
    if geo == 'france-metropolitan':
        communes = fm        
    
    if geo not in ['france-all', 'france-metropolitan']:
        
        list_dept_available = communes['departement_code'].unique()
        
        if all([dpt in list_dept_available for dpt in list_ovdep + ['29']]):
    
            dep29 =  communes[communes['departement_code'].isin(['29'])]
            minx = dep29['geometry'].bounds.minx.min()
            miny = dep29['geometry'].bounds.miny.min() + 3
            
            list_new_dep = []            
                
            
            for d in range(len(list_ovdep)):
                ovdep = communes[communes['departement_code'].isin([list_ovdep[d]])]
                
                if list_ovdep[d] == '973':
                    # area divided by 4 for Guyane
                    ovdep = _rescale_geom(df=ovdep, factor = 0.25)
                
                ovdep_bounds = ovdep['geometry'].bounds
                maxxdep = ovdep_bounds.maxx.max()
                maxydep = ovdep_bounds.maxy.max()
                xoff = minx - maxxdep - 2.5
                yoff = miny - maxydep
                ovdep['geometry'] = ovdep['geometry'].apply(lambda x: translate(x, xoff=xoff, yoff=yoff))
                
                miny = ovdep['geometry'].bounds.miny.min() - 1.5
                list_new_dep.append(ovdep)
            
            # PARIS
            paris = communes[communes['departement_code'].isin(['75','92', '93','94'])]
            paris = _rescale_geom(df = paris, factor = 4)
            
            dep29 =  communes[communes['departement_code'].isin(['29'])]
            minx = dep29['geometry'].bounds.minx.min()
            miny = dep29['geometry'].bounds.miny.min() + 3
            
            maxxdep = paris.bounds.maxx.max()
            maxydep = paris.bounds.maxy.max()
            xoff = minx - maxxdep + 1
            yoff = miny - maxydep - 5
            paris['geometry'] = paris['geometry'].apply(lambda x: translate(x, xoff=xoff, yoff=yoff))
              
            
            if geo == 'france-zoom-overseas-paris':        
                communes = pd.concat(list_new_dep + [fm] + [paris])
            elif geo == 'france-zoom-paris':
                communes = pd.concat([fm] + [paris])
            elif geo == 'france-zoom-overseas':
                 communes = pd.concat(list_new_dep + [fm])

    communes = communes.reset_index(drop=True)   
     
    return(communes)
            
   
            