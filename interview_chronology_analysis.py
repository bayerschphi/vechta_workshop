import json
import pandas as pd
import plotly.express as px
import warnings
import plotly
from plotly.subplots import make_subplots
import plotly.graph_objects as go
#import ipywidgets as ipw

warnings.simplefilter(action='ignore', category=FutureWarning)

force_chunk_nr_as_x_axis = False


def timecode_to_frames(tc, framerate):
    minutes = int(tc[:2]) * 60
    seconds = (minutes + int(tc[3:5])) * 60
    frames = (seconds + int(tc[6:8])) * framerate + int(tc[9:])
    return frames


def frames_to_timecode(frames, framerate):
    tc_fr = int(frames % framerate)
    if tc_fr < 10:
        tc_fr = '0' + str(tc_fr)
    tc_s = int((frames / framerate) % 60)
    if tc_s < 10:
        tc_s = '0' + str(tc_s)
    tc_m = int(frames / framerate / 60 % 60)
    if tc_m < 10:
        tc_m = '0' + str(tc_m)
    tc_h = int(frames / framerate / 60 / 60)
    if tc_h < 10:
        tc_h = '0' + str(tc_h)

    return str(tc_h) + ':' + str(tc_m) + ':' + str(tc_s) + '.' + str(tc_fr)


# with open("C:\\Users\\moebusd\\sciebo - Möbus, Dennis (moebusd@fernuni-hagen.de)@fernuni-hagen.sciebo.de\\OHD\\Data TM OHD\\OHD_complete_raw_100c_70t", 'r') as f:
#   data = json.load(f)
#
# all_interviews = []
#
# for archiv in data["corpus"]:
#   print(archiv)
#   for interview in data["corpus"][archiv]:
#     print('     '+interview)
#     all_interviews.append(interview) # Liste für Dropdown-Menü zur Auswahl des Interviews
# print(str(len(all_interviews)) + ' Interviews')
#
# input = input("Interview aus Liste wählen und hier hinein kopieren:")

def chronology_matrix(data, input: str="",  return_fig: bool = False, print_fig: bool = True, return_data: bool = False, topic_filter: bool = True, z_score: bool = False, threshold_top_filter: float=0.01, outlier_threshold: float=0.02): # @Philipp bitte Topic Filter als Schalter in Dash
    top_dic = data
    if type(top_dic) is not dict:
        top_dic = json.loads(top_dic)
    else:
        top_dic = top_dic
    interview_id = str(input)
    # print(interview_id)
    archive_id = str(input)[:3]
    dff = []
    chunk_counter = 0
    chunk_set = 0
    transfer = []
    threshold_top_filter = threshold_top_filter # ggf. als Regler
    outlier_threshold = outlier_threshold # ggf. als Regler
    top_filter = []

    for sents in top_dic["corpus"][interview_id[0:3]][interview_id]["sent"]:

        if top_dic["corpus"][interview_id[0:3]][interview_id]["sent"][sents]["chunk"] == chunk_set:
            transfer.append([top_dic["corpus"][interview_id[0:3]][interview_id]["sent"][sents]["tape"],
                             top_dic["corpus"][interview_id[0:3]][interview_id]["sent"][sents]["time"],
                             top_dic["corpus"][interview_id[0:3]][interview_id]["sent"][sents]["speaker"],
                             top_dic["corpus"][interview_id[0:3]][interview_id]["sent"][sents]["raw"],
                             top_dic["corpus"][interview_id[0:3]][interview_id]["sent"][sents]["chunk"]])
        if top_dic["corpus"][interview_id[0:3]][interview_id]["sent"][sents]["chunk"] != chunk_set:
            dff.append(transfer)
            chunk_set += 1
            transfer = []
            transfer.append([top_dic["corpus"][interview_id[0:3]][interview_id]["sent"][sents]["tape"],
                             top_dic["corpus"][interview_id[0:3]][interview_id]["sent"][sents]["time"],
                             top_dic["corpus"][interview_id[0:3]][interview_id]["sent"][sents]["speaker"],
                             top_dic["corpus"][interview_id[0:3]][interview_id]["sent"][sents]["raw"],
                             top_dic["corpus"][interview_id[0:3]][interview_id]["sent"][sents]["chunk"]])
    dff.append(transfer)

    # timecodes addieren
    try:
        if type(dff[0][0][1]) is not str or force_chunk_nr_as_x_axis:
            # print('No Timecode for X-Axis available, using index-nr of chunks')
            dff_2 = dff
            tc_indicator = False

        else:
            tape_counter = 1
            dff_2 = []
            time_set = 0
            tc_indicator = True
            for chunk in dff:
                # print(chunk)
                transfer_segments = []
                for segment in chunk:
                    # print(segment)
                    if tape_counter == int(segment[0]):
                        x = frames_to_timecode(timecode_to_frames(segment[1], 24) + time_set, 24)
                        transfer_segments.append([segment[0], x, segment[2], segment[3], segment[4]])
                    if tape_counter != int(segment[0]):
                        tape_counter += 1
                        time_set = timecode_to_frames(x, 24)
                        x = frames_to_timecode(timecode_to_frames(segment[1], 24) + time_set, 24)
                        transfer_segments.append([segment[0], x, segment[2], segment[3], segment[4]])
                dff_2.append(transfer_segments)
    except IndexError: # manche Transkripte sind scheinbar leer (zB ASG1224)
        return 'Transkript leer'


    # print(dff_2)

    results = []
    results_worddensity = []
    results_speaker_diffusion = []

    # alle Sprecher suchen

    speakers = []
    doc_wordcount = []

    for chunk in dff_2:
        for segment in chunk:
            if type(segment[2]) is not str:
                continue
            # print(segment)
            # doc_wordcount.append(len(segment[2].split(' ')))
            if segment[2] not in speakers:  # and segment[2] != '#'
                speakers.append(segment[2])
            else:
                continue
    # print(speakers)

    # Sprechanteile berechnen
    for chunk in dff_2:
        speakerdiffusion = []
        for speaker in speakers:
            count = 0
            for segment in chunk:
                # print(segment)
                if segment[2] == speaker:
                    count += len(str(segment[3]).split(' '))
            speakerdiffusion.append(count)
        results_speaker_diffusion.append(speakerdiffusion)
    # print(results_speaker_diffusion)

    final_results_speaker_diffusion = []
    wordcount = []
    for chunk in results_speaker_diffusion:
        counter = 0
        for count in chunk:
            counter += count
        wordcount.append(counter)

    for i, count in enumerate(results_speaker_diffusion):
        # print(wordcount[i])
        if tc_indicator:
            for j, speaker in enumerate(count):
                try:
                    final_results_speaker_diffusion.append(
                        [speakers[j], timecode_to_frames(dff_2[i][-1][1], 24) / 24 / 60, speaker / wordcount[i], i])
                except ZeroDivisionError:
                    final_results_speaker_diffusion.append(
                        [speakers[j], timecode_to_frames(dff_2[i][-1][1], 24) / 24 / 60, 1, i])
        else:
            for j, speaker in enumerate(count):
                try:
                    final_results_speaker_diffusion.append([speakers[j], i, speaker / wordcount[i]])
                except ZeroDivisionError:
                    final_results_speaker_diffusion.append([speakers[j], i, 1])

                    # Sprechgeschwindigkeit berechnen
    if tc_indicator:
        for i, chunk in enumerate(dff_2):
            time = (timecode_to_frames(chunk[-1][1], 24) - timecode_to_frames(chunk[0][1], 24)) / 24
            try:
                wordfreq = wordcount[i] / time
                results_worddensity.append(['worddensity', timecode_to_frames(chunk[-1][1], 24) / 24 / 60, wordfreq, i])
            except ZeroDivisionError:
                results_worddensity.append(['worddensity', timecode_to_frames(chunk[-1][1], 24) / 24 / 60, 1, i])

    ## Händisches Clustering -> Liste in Funktion übergeben und eigenen Schalter einfügen -
    # jetzt läuft es über den Topic Filter, der unten auskommentiert ist

    # Modell ohd_complete_240411_pre_70c_80t_corr

    clusters = [                        # Liste mit Listen mit Topicnummern, die zusammengefasst werden sollen
        ("01 Familie", [4, 5, 18, 61, 64, 69]),
        ("02 Privates", [3, 38, 50, 33, 44, 59, 66]),
        ("03 Freizeit", [1, 26, 27, 31, 56]),
        ("04 Bildung", [47, 34, 75]),
        ("05 Arbeit", [12, 13, 37, 46, 9, 62, 30]),
        ("06 Kultur", [74, 48, 32, 15, 11, 34]),
        ("07 Religion", [71, 42, 35]),
        ("08 Administratives", [2, 73]),
        ("09 Politik", [7, 23]),
        ("10 Bewegungen", [6, 21, 25]),
        ("11 Repression", [76, 70, 55, 20, 16]),
        ("12 Krieg", [0, 10, 28, 41, 63]),
        ("13 Mobilität", [43, 54, 68]),
        ("14 Internationales", [49, 58, 75, 57]),
        ("15 Belastungen", [8, 40, 45, 47]),
        ("16 Subjektivität", [77, 72, 65, 52, 53, 36]),
        ("17 Metaebene", [29, 60]),
    ]

    # Modell ohd_complete_70_80_vortrag

    # clusters = [                        # Liste mit Listen mit Topicnummern, die zusammengefasst werden sollen
    #     ("01 Familie", [41, 38, 13, 35, 70, 37]),
    #     ("02 Privates", [0, 32, 71, 50, 78, 15, 74]),
    #     ("03 Freizeit", [59, 42, 58]),
    #     ("04 Bildung", [47, 62, 34, 75]),
    #     ("05 Arbeit", [52, 73, 12, 56, 29, 27]),
    #     ("06 Kultur", [30, 28]),
    #     ("07 Religion", [40, 6, 25]),
    #     ("08 Finanzen", [65, 76]),
    #     ("09 Politik", [18, 20]),
    #     ("10 Bewegungen", [16, 21, 55, 72]),
    #     ("11 Repression", [3, 4, 24, 57, 63, 66]),
    #     ("12 Krieg", [14, 10, 26, 23, 46, 39, 62]),
    #     ("13 Mobilität/Orte", [7, 43, 67, 79]),
    #     ("14 Internationales", [31, 60, 68, 77]),
    #     ("15 Belastungen", [22, 19]),
    #     ("16 Subjektivität", [33, 51, 8, 48, 44, 69, 2]),
    #     ("17 Metaebene", [36, 11]),
    # ]

    topicweights = []

    if topic_filter:
        if tc_indicator:
            for nr, chunk in enumerate(dff_2):
                for nr_c, cluster in enumerate(clusters):
                    transfer = 0
                    for top in cluster[1]:
                        transfer += top_dic["weight"][interview_id[0:3]][interview_id][str(chunk[0][4])][str(top)]
                    topicweights.append([cluster[0], timecode_to_frames(chunk[-1][1], 24)/24/60, transfer/len(cluster), nr])
        else:
            for nr, chunk in enumerate(dff_2):
                for nr_c, cluster in enumerate(clusters):
                    transfer = 0
                    for top in cluster[1]:
                        transfer += top_dic["weight"][interview_id[0:3]][interview_id][str(chunk[0][4])][str(top)]
                    topicweights.append([cluster[0],nr , transfer/len(cluster)])



    else:
        if tc_indicator:
            for nr, chunk in enumerate(dff_2):
                for top in top_dic["weight"][interview_id[0:3]][interview_id][str(chunk[0][4])]:
                    topicweights.append([int(top), timecode_to_frames(chunk[-1][1], 24)/24/60, top_dic["weight"][interview_id[0:3]][interview_id][str(chunk[0][4])][top], nr])
        else:
            for nr, chunk in enumerate(dff_2):
                for top in top_dic["weight"][interview_id[0:3]][interview_id][str(chunk[0][4])]:
                    topicweights.append([int(top) ,nr , top_dic["weight"][interview_id[0:3]][interview_id][str(chunk[0][4])][top]])

    # Topic Weights
    ## Filter, um Heatmap konsistenter zu gestalten - niedrigschwellige Topic fliegen raus

    # if topic_filter:
    #     find_max = {}
    #     heat_dic = {}
    #     count = 0
    #     for c in top_dic["weight"][archive_id][interview_id]:
    #         count += 1
    #         for t in top_dic["weight"][archive_id][interview_id][c]:
    #             if t not in heat_dic:
    #                 heat_dic.update({t: top_dic["weight"][archive_id][interview_id][c][
    #                 t]})  # das int(t) muss genutzt werden, da das speichern in Store die Datei umwandelt
    #                 find_max.update({t: top_dic["weight"][archive_id][interview_id][c][t]})
    #
    #             else:
    #                 heat_dic.update({t: heat_dic[t] + top_dic["weight"][archive_id][interview_id][c][t]})
    #                 if top_dic["weight"][archive_id][interview_id][c][
    #                 t] > find_max[t]:
    #                     find_max.update({t: top_dic["weight"][archive_id][interview_id][c][t]})
    #                 else:
    #                     continue
    #
    #     for key, val in heat_dic.items():
    #         heat_dic.update({key: heat_dic[key] / count})
    #         if heat_dic[key] < threshold_top_filter:
    #             top_filter.append(key)
    #     #print(top_filter)
    #
    #     for key, val in find_max.items():
    #         if find_max[key] < outlier_threshold and key not in top_filter:
    #             top_filter.append(key)
    #     #print(top_filter)
    #
    # topicweights = []
    #
    # if tc_indicator:
    #   for nr, chunk in enumerate(dff_2):
    #     for top in top_dic["weight"][interview_id[0:3]][interview_id][str(chunk[0][4])]:
    #         if top not in top_filter:
    #             # topicweights.append([str(top) + ' ' + str([word[1] for word in top_dic["words"][top][:10]]), timecode_to_frames(chunk[-1][1], 24)/24/60, top_dic["weight"][interview_id[0:3]][interview_id][str(chunk[0][4])][top], nr])
    #             topicweights.append([int(top), timecode_to_frames(chunk[-1][1], 24)/24/60, top_dic["weight"][interview_id[0:3]][interview_id][str(chunk[0][4])][top], nr])
    #
    #         else:
    #             continue
    #
    #   #print(topicweights[1])
    # else:
    #   for nr, chunk in enumerate(dff_2):
    #     for top in top_dic["weight"][interview_id[0:3]][interview_id][str(chunk[0][4])]:
    #       #print(chunk[0][4])
    #       if top not in top_filter:
    #         # topicweights.append([str(top) + ' ' + str([word[1] for word in top_dic["words"][top][:10]]),nr , top_dic["weight"][interview_id[0:3]][interview_id][str(chunk[0][4])][top]])
    #         topicweights.append([int(top) ,nr , top_dic["weight"][interview_id[0:3]][interview_id][str(chunk[0][4])][top]])
    #       else:
    #         continue
    #   #print(topicweights[1])

    if tc_indicator:
        chronology_df = pd.DataFrame(topicweights, columns=['top', 'minute', 'weight',
                                                         'ind'])
    if tc_indicator == False:
        chronology_df = pd.DataFrame(topicweights, columns=['top', 'chunk', 'weight'])

    if return_data:
        chronology_list = chronology_df.values.tolist()
        #print(chronology_list[0])
        return chronology_list

    fig_final = make_subplots(rows=3, cols=1)

    # chronologische Verlaufsheatmap
    if tc_indicator:
        df_heatmap = pd.DataFrame(topicweights, columns=['top', 'minute', 'weight',
                                                         'ind'])  # kann man bei Timecode auf X-Achse Chunk-Nr. ins Hover schreiben? - ist in der Tabelle schon als "ind"
        doc_tops_heatmap = df_heatmap.pivot(index = "top", columns = "minute", values = "weight")

        if z_score == True:
            # Berechnung der z-Standardisierung
            mean = doc_tops_heatmap.mean()
            std_dev = doc_tops_heatmap.std()
            z_scores = ((doc_tops_heatmap - mean) / std_dev)

            doc_tops_heatmap = z_scores


    else:
        df_heatmap = pd.DataFrame(topicweights, columns=['top', 'chunk', 'weight'])
        doc_tops_heatmap = df_heatmap.pivot(index = "top", columns = "chunk", values = "weight")

        if z_score == True:
            # Berechnung der z-Standardisierung
            mean = doc_tops_heatmap.mean()
            std_dev = doc_tops_heatmap.std()
            z_scores = ((doc_tops_heatmap - mean) / std_dev)

            doc_tops_heatmap = z_scores

    fig_final.add_trace(go.Heatmap(z=doc_tops_heatmap, x=doc_tops_heatmap.columns, y=doc_tops_heatmap.index), row=1, col=1)
    fig_final.update_xaxes(visible=False, showticklabels=False, row=1, col=1)
    fig_final.update_yaxes(visible=True, showticklabels=True, type = "category", row=1, col=1) # type = "category": equal y-axis ticks bei uneven number steps


    # chronologische Speaker-Heatmap
    if tc_indicator:
        df_heatmap = pd.DataFrame(final_results_speaker_diffusion, columns=['top', 'minute', 'weight', 'ind'])
        doc_tops_heatmap = df_heatmap.pivot(index = "top", columns = "minute", values = "weight")
    else:
        df_heatmap = pd.DataFrame(final_results_speaker_diffusion, columns=['top', 'chunk', 'weight'])
        doc_tops_heatmap = df_heatmap.pivot(index = "top", columns= "chunk", values = "weight")
    fig_final.add_trace(go.Heatmap(z=doc_tops_heatmap, x=doc_tops_heatmap.columns, y=doc_tops_heatmap.index), row=2,col=1)
    fig_final.update_xaxes(visible=True, showticklabels=True, row=2,col=1)
    if tc_indicator:
        fig_final.update_xaxes(visible=False, showticklabels=False, row=2, col=1)
    fig_final.update_yaxes(visible=True, showticklabels=True, row=2,col=1)
    # fig_final.update(layout_coloraxis_showscale=False, row=2,col=1)

    #Worddensity
    if tc_indicator:
        df_heatmap = pd.DataFrame(results_worddensity, columns=['top', 'minute', 'weight', 'ind'])
        doc_tops_heatmap = df_heatmap.pivot(index = "top", columns = "minute", values = "weight")
        fig = px.imshow(doc_tops_heatmap, color_continuous_scale='dense',
                        aspect='auto')
        fig.update_xaxes(visible=False, showticklabels=False)
        fig.update_yaxes(visible=False, showticklabels=False)
        fig.update(layout_coloraxis_showscale=False)
        fig_final.add_trace(go.Heatmap(z=doc_tops_heatmap, x=doc_tops_heatmap.columns, y=doc_tops_heatmap.index), row=3,col=1)
        fig_final.update_xaxes(visible=True, showticklabels=True, row=3,col=1)
        fig_final.update_yaxes(visible=False, showticklabels=False, row=3,col=1)



    fig_final.update_traces(hovertemplate="Chunk: %{x}" "<br>Topic: %{y}" "<br>Weight: %{z}<extra></extra>", row=1,
                            col=1)
    if tc_indicator:
        fig_final.update_traces(hovertemplate="Time: %{x}" "<br>Topic: %{y}" "<br>Weight: %{z}<extra></extra>", row=1,
                                col=1)
    fig_final.update_traces(hovertemplate="Chunk: %{x}" "<br>Speaker: %{y} <extra></extra>" "<br>Weight: %{z}<extra>", row=2, col=1)
    if tc_indicator:
        fig_final.update_traces(hovertemplate="Time: %{x}" "<br>Speaker: %{y} <extra></extra>" "<br>Weight: %{z}<extra>", row=2, col=1)
    fig_final.update_traces(hovertemplate="Worddensity: %{x} <extra>", row=3, col=1)
    fig_final.update_traces(colorscale="dense")
    fig = fig_final
    fig['layout']['yaxis1'].update(domain=[0.16, 1.0])
    fig['layout']['yaxis2'].update(domain=[0.05, 0.15])
    fig['layout']['yaxis3'].update(domain=[0.0, 0.04])
    fig.update_traces(showlegend=False)
    fig.update_traces(showscale = False)
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    # fig.show()

    if return_fig:
        return fig, chronology_df, tc_indicator
    if print_fig:
        fig.show()


#chronology_matrix(input, data)