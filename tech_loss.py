#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy  as np

topo_df  = pd.read_csv('C://Users/ИТ ФИЦ/Desktop/Test/topo_2199 - topology.csv')                       .set_index('branch_id')
link_df  = topo_df[topo_df.type.isin(['Link'])]
equip_df = topo_df[topo_df.type.isin(['Link']) == False]

# Загрузка данных о приборах учета 
measure_unit = pd.read_csv('C://Users/ИТ ФИЦ/Desktop/Test/TS_2199/topo_2199 - measure_unit.csv')                .set_index('terminal_id')

# Загрузка данных о кабелях и их параметров
ac_line  = pd.read_csv('C://Users/ИТ ФИЦ/Desktop/Test/topo_2199 - line.csv')                .set_index('branch_id')
std_cable = pd.read_csv('C://Users/ИТ ФИЦ/Desktop/Test/TS_2199/topo_2199 - std_cable.csv')                .set_index('cable_type')

# Загрузка данных по показаниям активной мощности ПУ
meter_act = pd.read_csv('C://Users/ИТ ФИЦ/Desktop/Test/active_power.csv')                         .set_index('measure_id').T
# Загрузка данных по показаниям реактивной мощности ПУ
meter_react = pd.read_csv('C://Users/ИТ ФИЦ/Desktop/Test/reactive_power.csv')                         .set_index('measure_id').T

balance_group = topo_df.groupby('bg_num').get_group(1)

def node_group(branch_full):
    
    ### Функция, формирующая список смежных вершин - adjacency list ###
    
    dict_node = {}
    
    # и столбцы с начальными и конечными узлами
    branch_topo = branch_full[['node_start', 'node_end']]
    
    # получаем список уникальных узлов в соответствующих столбцах
    node_start_unique = branch_full.node_start.dropna().unique()
    node_end_unique   = branch_full.node_end.dropna().unique()
    
    # обобщенный список уникальных узлов балансовой группы
    ns_array = branch_full.node_start.dropna().to_numpy()
    ne_array = branch_full.node_start.dropna().to_numpy()
    
    node_unique = np.unique(np.append(ns_array, ne_array))
    
    # цикл по узлам в таблице node
    for node in node_unique:
        
        value = []
        
        # если узел в таблице узлов находится в списке уникальных начальных узлов ветвей,
        if node in node_start_unique:
            # то выбирается сооветствующий ему конечный узел (формат list)
            value_end = branch_topo[branch_topo.node_start == node].node_end.to_list()
            # и добавляется в обобщенную топологию ветвей этого узла
            value = value + value_end
        
        # если узел в таблице узлов находится в списке уникальных конечных узлов ветвей,
        if node in node_end_unique:
            # то добавляется сооветствующий ему начальный узел (формат list)
            value_start = branch_topo[branch_topo.node_end == node].node_start.to_list()
            # и добавляется в обобщенную топологию ветвей этого узла
            value = value + value_start
        
        # на выходе получаем словарь, где ключом является узел, а значением является список узлов
        dict_node[node] = value

    return dict_node

# Список входных терминалов балансовых групп
in_list1 = ['4ec22423-b389-403b-b4e0-b85a33f7832f',
            '48b2a15b-5838-4874-8461-d76587769de5',
            '95d13c84-eb63-45fa-b60b-b960c2c536e4',
            'ff760945-68fd-4780-97ce-c71a9e68d028']

in_list2 = ['84e3b2e5-3047-42ab-b7f3-3bfa762bb3eb',
            '990af4d2-060c-4a16-850d-93fd8fae72a9']

in_list3 = ['7ac6c580-21fc-4a35-bfb5-f5a5ea601dc0',
            '9b63114c-942a-40bb-a0be-ef7c059b626c',
            '2ce21189-8a08-4c14-92ce-f95cb9c5883b',
            '9b63114c-942a-40bb-a0be-ef7c059b626c']

in_list4 = ['df2dea8f-abbb-4ea9-bdb0-71e34451034a',
            '35ca9162-b0d7-4894-8f60-2768e897eb4e']

in_dict = {1 : in_list1,
           2 : in_list2,
           3 : in_list3,
           4 : in_list4}

cable_dict = {1 : 'АПвБбШп 4x185',
              2 : 'АСБ2л 4x95',
              3 : 'АСБ2л 4x95',
              4 : 'АПвБбШп 4x185'}

def r_temp(length, cable_type, current, t_allow, i_allow, r_ohm_km_20, cond_mater):
    ## Расчет активного сопротивления кабеля с учетом температуры 
    
    # Если жилы кабеля сделаны из алюминия, то температурный коэффициент
    if cond_mater == 'Алюминий':
        k_temp = 4.2e-3 
    else:
        # если из меди, то:
        k_temp = 4.3e-3
    
    # Зависимость активного сопротивления от температуры линейна 
    # (зависимость температуры от тока также принимается линейной с высокой точностью) 
    r_ohm_temp = r_ohm_km_20 + k_temp * (t_allow - 20) / i_allow * current
    
    return r_ohm_temp

def transformer_loss(s_rated, i_oc, u_sc, pfe, p_sc, act_kwh, react_kvarh):
    ## Расчет технических потерь в силовом трансформаторе
    
    # Определение потока полной мощности через силовой трансформатор
    s_kva = (act_kwh ** 2 + react_kvarh ** 2) ** 0.5
    # Определение коэффициента загрузки трансформатора
    k_load = s_kva / s_rated 
    
    # Определение потерь в силовом трансформаторе на передачу активной мощности
    # с учетом коэффициента загрузки трансформатора
    p_loss = pfe + p_sc * k_load ** 2
    
    # Определение потерь в силовом трансформаторе на передачу реактивной мощности
    # с учетом коэффициента загрузки трансформатора 
    q_loss = (i_oc + k_load * u_sc) / 100 * s_rated
    
    # Определение суммарных потерь с учетом экономического эквивалента 
    # реактивной мощности
    k_e = 0.08
    loss_full = p_loss + k_e * q_loss 
    
    return loss_full

def loss_calc(in_list, meter_act, meter_react, 
              adj_list, balance_group,
              ac_line, std_cable, cable_type):
    
    loss_20_df   = pd.DataFrame([], index = meter_act.index)
    loss_load_df = pd.DataFrame([], index = meter_act.index)
    n_list = []

    for m_term in in_list:
    
        # Получаем идентификатор ПУ, привязанного к терминалу
        meter_id = measure_unit[measure_unit.index == m_term]                .measure_id[0]
    
        # Получаем показания конкретного ПУ
        act_kwh     = meter_act[meter_id]
        react_kvarh = meter_react[meter_id]
    
        # Из списка смежных вершин балансовой группы получаем идентификаторы соседних узлов
        neigh_node = adj_list[m_term]
    
        r_list = []
        i_list = []
    
        for n_term in neigh_node:
        
            n_list.append(n_term)
        
            check_branch = balance_group.isin([m_term, n_term])
            branch_index = check_branch.loc[(check_branch.node_start == True) &
                                        (check_branch.node_end   == True)] \
                                       .index[0]
        
            # Поиск ветви в списке ветвей балансовой группы
            br_row  = balance_group[balance_group.index == branch_index]
            name    = br_row.name[0]
            br_type = br_row.type[0]
            
            # если класс оборудования соответствует КЛ, то
            if br_type == 'ACLineSegment':
                
                # Поиск данной линии в таблице линий с параметрами из СУПА
                line_row = ac_line[ac_line.index == branch_index]
                # длина кабеля, [км]
                length_km  = line_row.length_m[0] * 1e-3
                # класс напряжения, [кВ]
                voltage  = line_row.voltage[0]
                
                # Поиск данного маркоразмера кабеля в справочнике
                ct_row = std_cable[std_cable.index == cable_type]
                # Определение паспортных данных кабеля
                # погонного активного сопротивления, [Ом/км]
                r_ohm_km = ct_row.r_ohm_km_20[0]
                # длительно допустимый ток кабеля, [А]
                i_allow  = ct_row.i_allowable[0]
                # длительно допустимая температура кабеля, [град]
                t_allow  = ct_row.t_allowable[0]
                cond_mater = ct_row.conductor_material[0]
                
                # Расчет тока в линии, [А]
                current  = (act_kwh ** 2 + react_kvarh ** 2) ** 0.5 / voltage
                
                # Расчет активных потерь, [кВт]
                loss_20 = r_ohm_km * length_km * current ** 2 * 1e-3
                loss_20 = loss_20.rename(name)
                
                # Расчет активного сопротивления кабеля с учетом температуры
                r_ohm_temp = r_temp(length_km, cable_type, current, 
                                    t_allow, i_allow, r_ohm_km, 
                                    cond_mater)
                
                # Аналогичный расчет активных потерь, [кВт]
                loss_load = r_ohm_temp * length_km * current ** 2 * 1e-3
                loss_load = loss_load.rename(name)
            
                loss_20_df   = pd.concat([loss_20_df, loss_20], axis = 1)
                loss_load_df = pd.concat([loss_load_df, loss_load], axis = 1)
            
            # если класс оборудования соответствует силовому трансформатору, то
            elif br_type == 'PowerTransformer':
                loss_full = transformer_loss(s_rated, i_oc, u_sc, pfe, 
                                             p_sc, act_kwh, react_kvarh)
                
    return loss_20_df, loss_load_df

loss_20_df   = pd.DataFrame([], index = meter_act.index)
loss_load_df = pd.DataFrame([], index = meter_act.index)

for balance_num in topo_df.bg_num.unique():
    balance_group = topo_df.groupby('bg_num').get_group(balance_num)
    adj_list = node_group(branch_full = balance_group)
    in_list = in_dict[balance_num]
    cable_type = cable_dict[balance_num]
    
    full_loss = loss_calc(in_list = in_list, 
                          meter_act = meter_act, 
                          meter_react = meter_react, 
                          adj_list = adj_list, 
                          balance_group = balance_group, 
                          ac_line = ac_line, 
                          std_cable = std_cable, 
                          cable_type = cable_type)
    
    load_loss = full_loss[1]
    loss_20   = full_loss[0]
    
    loss_20_df   = pd.concat([loss_20_df, loss_20], axis = 1)
    loss_load_df = pd.concat([loss_load_df, load_loss], axis = 1)

loss_load_df.to_csv('C://Users/ИТ ФИЦ/Desktop/Test/loss_load.csv')
loss_20_df.to_csv('C://Users/ИТ ФИЦ/Desktop/Test/loss_20.csv')
