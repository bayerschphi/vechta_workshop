from interview_chronology_analysis import chronology_matrix
# from ohtm.preprocessing_functions.preprocess_outstr import *
import copy
import json
# import spacy
#from spacy_sentiws import spaCySentiWS

load_file_name = "ohd_complete_final_raw_preprocessed_lem_pos_off_75c_new_stop_50_500_5000"
#working_folder = "C:\\Users\\phili\\sciebo - Bayerschmidt, Philipp (bayerschmidt@fernuni-hagen.de)@fernuni-hagen.sciebo.de\\Topic Modeling\\main test\\github_test\\"
working_folder = "C:\\Users\\bayerschmidt\\sciebo - Bayerschmidt, Philipp (bayerschmidt@fernuni-hagen.de)@fernuni-hagen.sciebo.de\\Topic Modeling\\main test\\github_test\\"

#with open(working_folder + load_file_name) as f:
 #   top_dic = json.load(f)

# nlp = spacy.load('de_core_news_lg')
# nlp.add_pipe('sentiws', config={'sentiws_path': 'data/sentiws'})
def max_top_in_chunk(data, nr_of_top_topics):
    interview = []
    chunk_nr = 0
    sort_list = []

    for chunk in data:
        if len(chunk) > 3: # wenn Timecode vorliegt, hat die Tabelle vier Spalten
            #print('> 3')
            if chunk[3] == chunk_nr:
                #print(chunk[2], chunk[0], chunk[3])
                sort_list.append((chunk[2], int(chunk[0]), int(chunk[3])))
            else:
                sort_list.sort(reverse=True)
                interview.append(sorted(sort_list[:nr_of_top_topics], key=lambda interview: interview[1]))
                chunk_nr = chunk[3]
                sort_list = []
        else: # Tabelle ohne Timecoee hat nur drei Spalten
            if chunk[1] == chunk_nr:
                #print(chunk[2], chunk[0], chunk[1])
                sort_list.append((chunk[2], int(chunk[0]), int(chunk[1])))
            else:
                sort_list.sort(reverse=True)
                interview.append(sorted(sort_list[:nr_of_top_topics], key=lambda interview: interview[1]))
                chunk_nr = chunk[1]
                sort_list = []
    return interview


def top_tops_interview(top_dic, nr_top_tops, selection: type=list):

    top_tops_dic = {}
    if type(top_dic) is not dict:
        top_dic = json.loads(top_dic)
    else:
        top_dic = top_dic

    for archive in top_dic["weight"]:
        for i in top_dic["weight"][archive]:
            if i.lower() in selection:
                top_tops_dic[i] = {}
                count = 0
                for c in top_dic["weight"][archive][i]:
                    count += 1
                    for t in top_dic["weight"][archive][i][c]:
                        if t not in top_tops_dic[i]:
                            top_tops_dic[i].update({t: top_dic["weight"][archive][i][c][t]})  # das int(t) muss genutzt werden, da das speichern in Store die Datei umwandelt
                        else:
                            top_tops_dic[i].update({t: top_tops_dic[i][t] + top_dic["weight"][archive][i][c][t]})
                for entry in top_tops_dic[i]:
                    top_tops_dic[i].update({entry:top_tops_dic[i][entry] / count})
            else:
                continue

    top_tops_list = []
    for interview in top_tops_dic:
        #print(top_tops_dic[interview])
        top_tops_list.append([interview, sorted([(val, top) for top, val in top_tops_dic[interview].items()], reverse=True)])

    global_top_count = {}
    for interview in top_tops_list:
        for top in interview[1][:nr_top_tops]:
            if top[1] not in global_top_count:
                global_top_count[top[1]] = 1
            else:
                global_top_count[top[1]] += 1


    global_top_count_list = [(count, top) for top, count in global_top_count.items()]
    out = sorted(global_top_count_list, reverse=True)



    return top_tops_list, out
def vertical_correlation_matrix(top_dic, gross_nr_correlations_per_chunk: int = 2, enrich_json: bool = False):

    if type(top_dic) is not dict:
        top_dic = json.loads(top_dic)
    else:
        top_dic = top_dic

    NoM_data = []
    for archive in top_dic["corpus"]:
        for interview in top_dic["corpus"][archive]:
            # print(interview)
            try:
                NoM_data.append((interview, max_top_in_chunk(chronology_matrix(top_dic, input=interview, return_fig=False, print_fig=False, return_data=True, topic_filter=False),gross_nr_correlations_per_chunk)))
            except KeyError: # untersuchen
                # print('KeyError')
                continue
            except ValueError: # untersuchen
                # print('ValueError')
                continue
            except AttributeError: # untersuchen
                # print('AttributeError')
                continue
            except IndexError: # leeres Transkript
                continue


    correlations = {}
    interview_correlation_matrix = []
    for interview in NoM_data:
        interview_matrix = [interview[0], []]
        for chunk in interview[1]: # hier auch Lambda wie oben?
            chunk_matrix = []
            global_corr = ''
            for top in chunk:
                chunk_matrix.append(top[1])
                global_corr += f'-{top[1]}-'
            interview_matrix[1].append(chunk_matrix)
            if global_corr in correlations:
                correlations[global_corr]+=1
            if global_corr not in correlations:
                correlations[global_corr] = 1
        interview_correlation_matrix.append(interview_matrix)

    total_global_correlations = []
    for key, val in correlations.items():
        total_global_correlations.append((val, key))

                                                                            # Korrelationsmatrix (ICM) zur Rückverfolgung
                                                                            # der Korrelationen in die Interviewss und die
                                                                            # Auszählung der globalen Korrelationen (tgc) -> man könnte
                                                                            # das mit 2, 3 und 4 korrelierenden Topics berechnen
                                                                            # und mit ins jSon schreiben und im Dash an irgendeiner
                                                                            # Stelle zugänglich machen als explorativen Einstieg

    # die Option enrich_json speichert das icm und tgc im json und gibt es zurück

    if enrich_json == True:

        if "correlation" not in top_dic:
            top_dic["correlation"] = {}
        if "vertical" not in top_dic["correlation"]:
            top_dic["correlation"]["vertical"] = {}
        if "interview_correlation_matrix" not in top_dic["correlation"]["vertical"]:
            top_dic["correlation"]["vertical"]["interview_correlation_matrix"] ={}
        if "total_global_correlations" not in top_dic["correlation"]["vertical"]:
            top_dic["correlation"]["vertical"]["total_global_correlations"] ={}
        top_dic["correlation"]["vertical"]["interview_correlation_matrix"][gross_nr_correlations_per_chunk] = interview_correlation_matrix
        top_dic["correlation"]["vertical"]["total_global_correlations"][gross_nr_correlations_per_chunk] = total_global_correlations

        return top_dic
    else:
        return interview_correlation_matrix, total_global_correlations




def horizontal_correlation_matrix(top_dic, enrich_json: bool = False):
    if type(top_dic) is not dict:
        top_dic = json.loads(top_dic)
    else:
        top_dic = top_dic

    NoM_data = []
    for archive in top_dic["corpus"]:
        for interview in top_dic["corpus"][archive]:
            # print(interview)
            try:
                NoM_data.append((interview, max_top_in_chunk(chronology_matrix(top_dic, input=interview, return_fig=False, print_fig=False, return_data=True, topic_filter=False), 1)))
            except KeyError: # untersuchen
                # print('KeyError')
                continue
            except ValueError: # untersuchen
                # print('ValueError')
                continue
            except AttributeError: # untersuchen
                # print('AttributeError')
                continue
            except IndexError: # leeres Transkript
                continue


    correlations = {}
    interview_correlation_matrix = []
    for interview in NoM_data:
        interview_matrix = [interview, []]
        for i, chunk in enumerate(interview[1][:len(interview[1])-1]):
            interview_matrix[1].append((interview[1][i][0][1], interview[1][i+1][0][1]))
            if interview[1][i][0][1] != interview[1][i+1][0][1]:
                if f'-{interview[1][i][0][1]}-{interview[1][i+1][0][1]}-' in correlations:
                    correlations[f'-{interview[1][i][0][1]}-{interview[1][i+1][0][1]}-'] += 1
                if f'-{interview[1][i][0][1]}-{interview[1][i+1][0][1]}-' not in correlations:
                    correlations[f'-{interview[1][i][0][1]}-{interview[1][i+1][0][1]}-'] = 1
            else:
                continue
        interview_correlation_matrix.append(interview_matrix)

    total_global_correlations = []
    for key, val in correlations.items():
        total_global_correlations.append((val, key))

    # die Option enrich_json speichert das icm und tgc im json und gibt es zurück

    if enrich_json == True:
        if "correlation" not in top_dic:
            top_dic["correlation"] = {}
        if "horizontal" not in top_dic["correlation"]:
            top_dic["correlation"]["horizontal"] = {}
        if "interview_correlation_matrix" not in top_dic["correlation"]["horizontal"]:
            top_dic["correlation"]["horizontal"]["interview_correlation_matrix"] = {}
        if "total_global_correlations" not in top_dic["correlation"]["horizontal"]:
            top_dic["correlation"]["horizontal"]["total_global_correlations"] = {}
        top_dic["correlation"]["horizontal"]["interview_correlation_matrix"] = interview_correlation_matrix
        top_dic["correlation"]["horizontal"]["total_global_correlations"]= total_global_correlations

        return top_dic
    else:
        return interview_correlation_matrix, total_global_correlations
def top_global_correlations(total_global_correlations, len_list: type = int):   # tgc aus json auslesen, man könnte in Dashboard "len_list" als
                                                                                # Schalter einbauen
    top_global_correlations = [line for line in sorted(total_global_correlations, reverse=True)[:len_list]]
    return top_global_correlations
def global_vertical_correlation_search(top_global_correlations, interview_correlation_matrix, t1, t2, t3=None, t4= None): # auf Seite Text Search; tgc, icm aus json auslesen

    if t4:
        results = [line for line in top_global_correlations if f'-{t1}-' in line[1] and f'-{t2}-' in line[1] and f'-{t3}-' in line[1] and f'-{t4}-' in line[1]]

    if t3 and not t4:
        results = [line for line in top_global_correlations if f'-{t1}-' in line[1] and f'-{t2}-' in line[1] and f'-{t3}-' in line[1]]

    else:
        results = [line for line in top_global_correlations if f'-{t1}-' in line[1] and f'-{t2}-' in line[1]]


    for nr_i, interview in enumerate(interview_correlation_matrix):
        for nr_c, chunk in enumerate(interview[1]):

            if t4:
                if t1 in chunk and t2 in chunk and t3 in chunk and t4 in chunk:
                    print(interview_correlation_matrix[nr_i][0], nr_c)

            if t3 and not t4:
                if t1 in chunk and t2 in chunk and t3 in chunk:
                    print(interview_correlation_matrix[nr_i][0], nr_c)
            else:
                if t1 in chunk and t2 in chunk:
                    print(interview_correlation_matrix[nr_i][0], nr_c)


def global_horizontal_correlation_search(total_global_correlations, interview_correlation_matrix, t1 = None, t2 = None): # auf Seite Text Search; tgc, icm aus json auslesen

    if t2:
        results = [line for line in total_global_correlations if f'-{t1}-' in line[1] and f'-{t2}-' in line[1]]

    else:
        results = [line for line in total_global_correlations if f'-{t1}-' in line[1]]


    for nr_i, interview in enumerate(interview_correlation_matrix):
        for nr_c, chunk in enumerate(interview[1]):
            if t2:
                if t1 in chunk and t2 in chunk:
                    print(interview_correlation_matrix[nr_i][0][0], nr_c)
            else:
                if t1 in chunk:
                    print(interview_correlation_matrix[nr_i][0][0], nr_c)


# die Funktionen top_global_correlations, global_vertical_correlation_search, global_horizontal_correlation_search
# angepasst an das angereicherte JSON

def top_global_correlations_json(top_dic, len_list: type = int, horizontal: bool =False, vertical:bool=False, gross_nr_correlations_per_chunk: int = 2):

    if type(top_dic) is not dict:
        top_dic = json.loads(top_dic)
    else:
        top_dic = top_dic

    if horizontal == True:
        total_global_correlations = top_dic["correlation"]["horizontal"]["total_global_correlations"]

    if vertical == True:
        total_global_correlations= top_dic["correlation"]["vertical"]["total_global_correlations"][str(gross_nr_correlations_per_chunk)]


    top_global_correlations = [line for line in sorted(total_global_correlations, reverse=True)[:len_list]]
    return top_global_correlations

def global_vertical_correlation_search_json(top_dic, t1, t2, t3=None, t4= None, return_search: bool = True): # auf Seite Text Search; tgc, icm aus json auslesen

    if type(top_dic) is not dict:
        top_dic = json.loads(top_dic)
    else:
        top_dic = top_dic


    if t4:
        top_global_correlations = top_dic["correlation"]["vertical"]["total_global_correlations"]["4"]
        interview_correlation_matrix = top_dic["correlation"]["vertical"]["interview_correlation_matrix"]["4"]
        results = [line for line in top_global_correlations if f'-{t1}-' in line[1] and f'-{t2}-' in line[1] and f'-{t3}-' in line[1] and f'-{t4}-' in line[1]]

    if t3 and not t4:
        top_global_correlations = top_dic["correlation"]["vertical"]["total_global_correlations"]["3"]
        interview_correlation_matrix = top_dic["correlation"]["vertical"]["interview_correlation_matrix"]["3"]
        results = [line for line in top_global_correlations if f'-{t1}-' in line[1] and f'-{t2}-' in line[1] and f'-{t3}-' in line[1]]

    else:
        top_global_correlations = top_dic["correlation"]["vertical"]["total_global_correlations"]["2"]
        interview_correlation_matrix = top_dic["correlation"]["vertical"]["interview_correlation_matrix"]["2"]
        results = [line for line in top_global_correlations if f'-{t1}-' in line[1] and f'-{t2}-' in line[1]]

# Für das Dashboard muss das Ergebnis als Variable zurückgegeben werden
    if return_search == True:
        search_result = []
        for nr_i, interview in enumerate(interview_correlation_matrix):
            for nr_c, chunk in enumerate(interview[1]):

                if t4:
                    if t1 in chunk and t2 in chunk and t3 in chunk and t4 in chunk:
                        result = (interview_correlation_matrix[nr_i][0], nr_c)
                        search_result.append(result)

                if t3 and not t4:
                    if t1 in chunk and t2 in chunk and t3 in chunk:
                        result = (interview_correlation_matrix[nr_i][0], nr_c)
                        search_result.append(result)

                else:
                    if t1 in chunk and t2 in chunk:
                        result = (interview_correlation_matrix[nr_i][0], nr_c)
                        search_result.append(result)

        return(search_result)

    else:
        for nr_i, interview in enumerate(interview_correlation_matrix):
            for nr_c, chunk in enumerate(interview[1]):

                if t4:
                    if t1 in chunk and t2 in chunk and t3 in chunk and t4 in chunk:
                        print(interview_correlation_matrix[nr_i][0], nr_c)

                if t3 and not t4:
                    if t1 in chunk and t2 in chunk and t3 in chunk:
                        print(interview_correlation_matrix[nr_i][0], nr_c)
                else:
                    if t1 in chunk and t2 in chunk:
                        print(interview_correlation_matrix[nr_i][0], nr_c)

def global_horizontal_correlation_search_json(top_dic, t1 = None, t2 = None, return_search: bool = True): # auf Seite Text Search; tgc, icm aus json auslesen

    if type(top_dic) is not dict:
        top_dic = json.loads(top_dic)
    else:
        top_dic = top_dic

    interview_correlation_matrix= top_dic["correlation"]["horizontal"]["interview_correlation_matrix"]
    total_global_correlations= top_dic["correlation"]["horizontal"]["total_global_correlations"]

    if t2:
        results = [line for line in total_global_correlations if f'-{t1}-' in line[1] and f'-{t2}-' in line[1]]

    else:
        results = [line for line in total_global_correlations if f'-{t1}-' in line[1]]

    if return_search == True:
        search_result = []
        for nr_i, interview in enumerate(interview_correlation_matrix):
            for nr_c, chunk in enumerate(interview[1]):
                if t2:
                    if t1 in chunk and t2 in chunk:
                        result = (interview_correlation_matrix[nr_i][0][0], nr_c)
                        search_result.append(result)
                else:
                    if t1 in chunk:
                        result = (interview_correlation_matrix[nr_i][0][0], nr_c)
                        search_result.append(result)

        return search_result
    else:


        for nr_i, interview in enumerate(interview_correlation_matrix):
            for nr_c, chunk in enumerate(interview[1]):
                if t2:
                    if t1 in chunk and t2 in chunk:
                        print(interview_correlation_matrix[nr_i][0][0], nr_c)
                else:
                    if t1 in chunk:
                        print(interview_correlation_matrix[nr_i][0][0], nr_c)


def emotions(top_dic, Input):
    working_folder = "C:\\Users\\moebusd\\sciebo - Möbus, Dennis (moebusd@fernuni-hagen.de)@fernuni-hagen.sciebo.de\\OHD\\Data TM OHD\\"

    ekel = [word for word in open(working_folder+"ekel.txt", mode='r', encoding = 'ANSI').read().split()]
    freude = [word for word in open(working_folder+"freude.txt", mode='r', encoding = 'ANSI').read().split()]
    furcht = [word for word in open(working_folder+"furcht.txt", mode='r', encoding = 'ANSI').read().split()]
    trauer = [word for word in open(working_folder+"trauer.txt", mode='r', encoding = 'ANSI').read().split()]
    verachtung = [word for word in open(working_folder+"verachtung.txt", mode='r', encoding = 'ANSI').read().split()]
    wut = [word for word in open(working_folder+"wut.txt", mode='r', encoding = 'ANSI').read().split()]




    interview = [Input, [], [], [], [], [], []]
    for nr in top_dic["corpus"][Input[:3]][Input]["sent"]:

                text = copy.deepcopy(top_dic["corpus"][Input[:3]][Input]["sent"][nr]["raw"])
                doc = nlp(str(text))
                text = str(text).lower()
                text_unified = text.replace('!', '. ').replace('?', '. ').replace(';', '. ').replace('...,',', ').replace(
                            '..,', ', ').replace('"', ' ').replace("'", ' ').replace("\n", ' ').replace(" - ", " ")
                pre_line = preprocess_outstr(text)
                data_out = pre_line.split(" ") # Tokenisierung
                counter = 0
                print(data_out)
                interview[1].append(len([word for word in ekel if word.lower() in data_out]))
                interview[2].append(len([word for word in freude if word.lower() in data_out]))
                interview[3].append(len([word for word in furcht if word.lower() in data_out]))
                interview[4].append(len([word for word in trauer if word.lower() in data_out]))
                interview[5].append(len([word for word in verachtung if word.lower() in data_out]))
                interview[6].append(len([word for word in wut if word.lower() in data_out]))
                for token in doc:
                    print('{}, {}, {}'.format(token.text, token._.sentiws, token.pos_))
                #for word in freude:
                #    if word in data_out:
                #        counter += 1
                #interview[1].append(counter)


    for emo in interview[1:]:
        print(emo[:30])




############################
########## TEST ############
############################

##################### vertical ########################################
#
# icm, tgc = vertical_correlation_matrix(top_dic, 3)

# top_dic = vertical_correlation_matrix(top_dic, 2, enrich_json=True)
#
# top_corrs = top_global_correlations(top_dic, 30)
#
#
# print(global_vertical_correlation_search_json(top_dic, 5, 23, return_search=True))
# print("______________________________________________")
# global_vertical_correlation_search_json(top_dic, 5, 23, return_search=False)


####################### horizontal #######################################

# icm, tgc = horizontal_correlation_matrix(top_dic)
#
# top_corrs = top_global_correlations(tgc, 30)
#
# for line in top_corrs:
#    print(line)
#
# print('Horizontale Korrelationen: ')
# global_horizontal_correlation_search(tgc, icm, t1=15, t2=15)

# selection_list_female = ['adg0001',
# 'adg0002',
# 'adg0004',
# 'adg0007',
# 'adg0010',
# 'adg0012',
# 'adg0018',
# 'adg0020',
# 'adg0022',
# 'adg0024',
# 'adg0025',
# 'adg0026',
# 'adg0027',
# 'adg0028',
# 'adg0029',
# 'adg0030',
# 'adg0032',
# 'adg0033',
# 'adg0037',
# 'adg0039',
# 'adg3175',
# 'adg3186',
# 'adg2917',
# 'adg2919',
# 'adg2924',
# 'adg2926',
# 'adg2988',
# 'adg2990',
# 'adg2991',
# 'adg2997',
# 'adg2998',
# 'adg3002',
# 'adg3046',
# 'adg2619',
# 'adg2620',
# 'adg2625',
# 'adg2438',
# 'adg2457',
# 'adg2460',
# 'adg2956',
# 'adg2957',
# 'adg2959',
# 'adg2964',
# 'adg2966',
# 'adg2970',
# 'adg1987',
# 'adg1990',
# 'adg1996',
# 'adg1997',
# 'adg1998',
# ]
#
# selection_list_male = [
# 'adg0003',
# 'adg0005',
# 'adg0006',
# 'adg0008',
# 'adg0009',
# 'adg0011',
# 'adg0013',
# 'adg0015',
# 'adg0016',
# 'adg0017',
# 'adg0019',
# 'adg0021',
# 'adg0023',
# 'adg0031',
# 'adg0034',
# 'adg0035',
# 'adg0036',
# 'adg0038',
# 'adg0041',
# 'adg0043',
# 'adg1986',
# 'adg1992',
# 'adg1994',
# 'adg1995',
# 'adg1999',
# 'adg2422',
# 'adg2423',
# 'adg2424',
# 'adg2621',
# 'adg2622',
# 'adg2623',
# 'adg2908',
# 'adg2909',
# 'adg2910',
# 'adg2911',
# 'adg2955',
# 'adg2958',
# 'adg2960',
# 'adg2961',
# 'adg2962',
# 'adg2963',
# 'adg2981',
# 'adg2983',
# 'adg2984',
# 'adg2989',
# 'adg2992',
# 'adg2993',
# 'adg2994',
# 'adg3176',
# 'adg3177'
# ]
#
# selection_list_male_lusir = [
# 'adg0003',
# 'adg0005',
# 'adg0006',
# 'adg0008',
# 'adg0009',
# 'adg0011',
# 'adg0013',
# 'adg0015',
# 'adg0016',
# 'adg0017',
# 'adg0019',
# 'adg0021',
# 'adg0023',
# 'adg0031',
# 'adg0034',
# 'adg0035',
# 'adg0036',
# 'adg0038',
# 'adg0041',
# 'adg0043'
#     ]
#
# selection_list_female_lusir = ['adg0001',
# 'adg0002',
# 'adg0004',
# 'adg0007',
# 'adg0010',
# 'adg0012',
# 'adg0018',
# 'adg0020',
# 'adg0022',
# 'adg0024',
# 'adg0025',
# 'adg0026',
# 'adg0027',
# 'adg0028',
# 'adg0029',
# 'adg0030',
# 'adg0032',
# 'adg0033',
# 'adg0037',
# 'adg0039']
#
# selection_list_male_ohne_lusir = [
# 'adg1986',
# 'adg1992',
# 'adg1994',
# 'adg1995',
# 'adg1999',
# 'adg2422',
# 'adg2423',
# 'adg2424',
# 'adg2621',
# 'adg2622',
# 'adg2623',
# 'adg2908',
# 'adg2909',
# 'adg2910',
# 'adg2911',
# 'adg2955',
# 'adg2958',
# 'adg2960',
# 'adg2961',
# 'adg2962',
# 'adg2963',
# 'adg2981',
# 'adg2983',
# 'adg2984',
# 'adg2989',
# 'adg2992',
# 'adg2993',
# 'adg2994',
# 'adg3176',
# 'adg3177'
# ]
#
# selection_list_female_ohne_lusir = [
# 'adg3175',
# 'adg3186',
# 'adg2917',
# 'adg2919',
# 'adg2924',
# 'adg2926',
# 'adg2988',
# 'adg2990',
# 'adg2991',
# 'adg2997',
# 'adg2998',
# 'adg3002',
# 'adg3046',
# 'adg2619',
# 'adg2620',
# 'adg2625',
# 'adg2438',
# 'adg2457',
# 'adg2460',
# 'adg2956',
# 'adg2957',
# 'adg2959',
# 'adg2964',
# 'adg2966',
# 'adg2970',
# 'adg1987',
# 'adg1990',
# 'adg1996',
# 'adg1997',
# 'adg1998',
# ]

#top_tops, global_tops = top_tops_interview(top_dic, 5, selection_list_female_ohne_lusir)

#for line in top_tops:
#        print(line)

#for line in global_tops:
#    print(line)

# emotions(top_dic, "ADG0001")