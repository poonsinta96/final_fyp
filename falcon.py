from first_cell import First_cell
from second_cell import Second_cell
from rule_cell import Rule_cell
from fourth_cell import Fourth_cell
from fifth_cell import Fifth_cell
from bullbear_cell import Bullbear_cell

from rule_methods import rules_needed, create_compound_arr, rules_label

import numpy as np
import math
import matplotlib.pyplot as plt
from graphviz import Digraph


class Falcon:
    def __init__(self, input_size, output_size):
        #initialisation
        self.ip = input_size
        self.op = output_size

        self.layer1 = [First_cell(x) for x in range(self.ip)]
        self.layer2 = [[Second_cell(stream = x, label= 0)] for x in range(self.ip)]
        self.layer3 = [{}]          
        self.layer4 = [[Fourth_cell(stream = x, label= 0)] for x in range(self.op)]
        self.layer5 = [Fifth_cell(x) for x in range(self.op)]

        self.bull_cell = Bullbear_cell()
        self.bear_cell = Bullbear_cell()

        self.VIGILANCE_PARA = 0.5 #decides how many cluster to be made- the higher the parameter is, the smaller the range of the set
        self.MOMENTUM = 0.5
        self.LEARNING_PARA = 0.5

        self.bullbear_index = 0.5

    
    def vigilanceTest(self, clusters, x_or_y):
        #IGNORE - keep for future reference
        sum_of_uv_diff = 0
        sum_of_maxi = 0

        if x_or_y == 'x':
            cur_layer = self.layer2
        elif x_or_y == 'y':
            cur_layer = self.layer4

        for stream_index in range(len(cur_layer)):
            stream = cur_layer[stream_index]
            cluster = clusters[stream_index]
            cur_cell = stream[cluster]

            u,v = cur_cell.get_uv()
            uv_diff = v-u
            sum_of_uv_diff += uv_diff

            maxi = abs(cur_cell.get_cur_maxi())
            sum_of_maxi += maxi

        #print(sum_of_uv_diff, (1-self.VIGILANCE_PARA) * sum_of_maxi)
        if sum_of_uv_diff <= (1-self.VIGILANCE_PARA) * sum_of_maxi:
            return True #True means pass vigilance test
        
        else:
            return False
             
    def rule_computation(self,rule_list, z24_list, null_list, ip_cluster_size):
        #IGNORE - keep for future reference

        #iterate through  the rule_list to calculate all the firing strength
        max_firing_strength = -1
        max_rule = ''
        y_cluster_firing=[0 for x in range(ip_cluster_size)]

        for rule in rule_list:
            #skip this rule if it is in the null_list - ie the rules which failed the vigilance test previously
            if rule in null_list:
                continue

            cur_cell_rule = self.layer3.get(rule, 0)
            #if rule_cell doesnt exist, create one
            if cur_cell_rule ==0:
                self.layer3[rule] = Rule_cell(label= rule,ip_size =self.ip)
                cur_cell_rule = self.layer3.get(rule)


            cluster_indexes = [int(y) for y in rule.split('/')[1:-1]] 
            
            firing_strength_arr = []
            for stream_index in range(len(z24_list)):
                stream = z24_list[stream_index]
                cluster_index = cluster_indexes[stream_index]
                stream_firing = stream[cluster_index]
                firing_strength_arr.append(stream_firing)
            

            firing_strength_x = firing_strength_arr[:self.ip]
            firing_strength_y = firing_strength_arr[self.ip:]
            
            #print("RULE",rule,':' ,firing_strength_x,firing_strength_y)

            firing_strength = cur_cell_rule.get_fs_xy(firing_strength_x, firing_strength_y)
            
            if firing_strength >= max_firing_strength:
                max_firing_strength = firing_strength
                max_rule = rule

            #update the max firing strength for others
            y_cluster = cluster_indexes[-1]
            if firing_strength > y_cluster_firing[y_cluster]:
                y_cluster_firing[y_cluster] = firing_strength

        #if there is no more rules to consider
        if max_rule == '':
            return '', -1, [], [],[]

        winning_input_cluster = self.layer3[max_rule].get_xcluster()
        winning_output_cluster = self.layer3[max_rule].get_ycluster()
        print('max_rule:', max_rule, 'with firing strength of', max_firing_strength, 'y_cluster_firing', y_cluster_firing)


        return max_rule, max_firing_strength,winning_input_cluster, winning_output_cluster, y_cluster_firing

    def max_rule_construction(self, bullbear ,x_list, y_list):
        ans = ''
        winning_input_cluster = []
        winning_output_cluster = []
    
        ans += bullbear
        ans += '/'
        
        for x_arr in x_list:
            x_add = np.argmax(x_arr)
            ans+= str(x_add)
            ans+= '/'
            winning_input_cluster.append(x_add)

        for y_arr in y_list:
            y_add = np.argmax(y_arr)
            ans += str(y_add)
            ans += '/'
            winning_output_cluster.append(y_add)

        if len(self.layer3)-1 < y_add:
            self.layer3.append({})

        cur_cell_rule = self.layer3[y_add].get(ans, 0)
        #if rule_cell doesnt exist, create one
        if cur_cell_rule ==0:
            self.layer3[y_add][ans] = Rule_cell(label= ans,ip_size =self.ip)
            cur_cell_rule = self.layer3[y_add].get(ans)
            #x=input(ans + ' is the rule to be created')

        max_rule_name = ans
        max_rule_cell = cur_cell_rule

        

        return max_rule_name, max_rule_cell, winning_input_cluster, winning_output_cluster

    def rule_fs_computation(self, rule, z24_list, cur_cell_rule):
            cluster_indexes = [int(y) for y in rule.split('/')[1:-1]] 
            
            firing_strength_arr = []
            for stream_index in range(len(z24_list)):
                stream = z24_list[stream_index]
                cluster_index = cluster_indexes[stream_index]
                stream_firing = stream[cluster_index]
                firing_strength_arr.append(stream_firing)
            

            firing_strength_x = firing_strength_arr[:self.ip]
            firing_strength_y = firing_strength_arr[self.ip:]
            

            firing_strength = cur_cell_rule.get_fs_xy(firing_strength_x, firing_strength_y)
            #print("RULE",rule,':' ,firing_strength,firing_strength_x,firing_strength_y)

            return firing_strength

    def train(self, train_set, original_add):
        x_train = train_set[:, :-(self.op+1)]
        y_train = train_set[:, self.ip:-(self.op)]
        bullbear_train= train_set[:, -1]

        bb_arr =[]
        real_ans_arr = []

        #x_train[2,2] = 2000 #just for simlutaion
        #y_train[2,0] = 300
        #training loop - should be 14588
        limit = 14588
        iter = 0
        while  iter < limit:
            print('ITER :', iter)
            if bullbear_train[iter] == 1:
                bullbear = 'Bull'
            else:
                bullbear = 'Bear'

            #feeding data to LAYER ONE 
            z1_list = []
            x_list = []
            for ip_num in range(len(self.layer1)):
                uv_list,z = self.layer1[ip_num].s_upward_flow_in(x_train[iter][ip_num])
                z1_list += [uv_list]
                x_list += [z]
            
            print('this is x: ',x_list)
            print('this is z1:',z1_list) #to see how data is passed from layer 1 to layer 2.

            #feedin data to LAYER TWO 
            z2_list = []
            #iterate through the stream
            for stream_index in range(len(z1_list)):
                stream = z1_list[stream_index]
                net = x_list[stream_index]

                #data flow in to LAYER TWO cells
                stream_z2 = []
                for cell_index in range(len(stream)):
                    uv_pair = stream[cell_index]
                    z2 = self.layer2[stream_index][cell_index].upward_flow_in(net, uv_pair)
                    stream_z2.append(z2)
                
                z2_list.append(stream_z2)

            print('this is z2_list: ',z2_list)




            #feeding data to LAYER FIVE 
            z5_list = []
            y_list = []
            for ip_num in range(len(self.layer5)):
                uv_list,z = self.layer5[ip_num].downward_flow_in(y_train[iter][ip_num])
                z5_list += [uv_list]
                y_list += [z]
            
            print('this is y: ',y_list)
            print('this is z5:',z5_list) #to see how data is passed from layer 1 to layer 2.

            #feedin data to LAYER FOUR 
            z4_list = []
            #iterate through the stream
            for stream_index in range(len(z5_list)):
                stream = z5_list[stream_index]
                net = y_list[stream_index]

                #data flow in to LAYER TWO cells
                stream_z4 = []
                for cell_index in range(len(stream)):
                    uv_pair = stream[cell_index]
                    z4 = self.layer4[stream_index][cell_index].downward_flow_in(net, uv_pair)
                    stream_z4.append(z4)
                
                z4_list.append(stream_z4)

            print('this is z4_list: ',z4_list)



            #construct max rule 
            max_rule_name, max_rule,winning_input_cluster, winning_output_cluster = self.max_rule_construction(bullbear ,z2_list, z4_list )
            z24_list = create_compound_arr(z2_list, z4_list)
            max_firing_strength = self.rule_fs_computation(max_rule_name, z24_list,max_rule)



            if max_firing_strength == 0 or max(z4_list[0]) == 0:
                print('====================FAIL MAX FIRING STRENGTH====================')
                print('')
                #check all the x values
                for stream_index in range(len(z2_list)):
                    if max(z2_list[stream_index]) == 0:
                        self.layer1[stream_index].create_cluster(x_list[stream_index])
                        self.layer2[stream_index].append(Second_cell(stream_index,len(self.layer2[stream_index])))
                
                #check all the y values
                for stream_index in range(len(z4_list)):
                    if max(z4_list[stream_index]) == 0:
                        self.layer5[stream_index].create_cluster(y_list[stream_index])
                        self.layer4[stream_index].append(Fourth_cell(stream_index,len(self.layer4[stream_index])))
                continue


            #update winning clusters
            #updating layer 1 - uv_pair and layer 2 - fuzziness
            for cell_index in range(len(self.layer1)):
                new_uv_pair = self.layer1[cell_index].learn(winning_input_cluster[cell_index], x_list[cell_index])
                self.layer2[cell_index][winning_input_cluster[cell_index]].learn(x_list[cell_index],new_uv_pair)
            #updating layer 5 - uv_pair and layer 4 - fuzziness
            for cell_index in range(len(self.layer5)):
                new_uv_pair = self.layer5[cell_index].learn(winning_output_cluster[cell_index], y_list[cell_index])
                self.layer4[cell_index][winning_output_cluster[cell_index]].learn(y_list[cell_index],new_uv_pair)

            y_index = winning_output_cluster[0]
            #self.layer3[y_index][max_rule_name].reward()

        #=======================================================================================================================================================#
            print('PARAMETER LEARNING')
            #feeding data to LAYER ONE 
            z1_list = []
            x_list = []
            for ip_num in range(len(self.layer1)):
                uv_list,z = self.layer1[ip_num].upward_flow_in(x_train[iter][ip_num])
                z1_list += [uv_list]
                x_list += [z]
            
            print('this is x: ',x_list)
            print('this is z1:',z1_list) #to see how data is passed from layer 1 to layer 2.

            #feedin data to LAYER TWO 
            z2_list = []
            #iterate through the stream
            for stream_index in range(len(z1_list)):
                stream = z1_list[stream_index]
                net = x_list[stream_index]

                #data flow in to LAYER TWO cells
                stream_z2 = []
                for cell_index in range(len(stream)):
                    uv_pair = stream[cell_index]
                    z2 = self.layer2[stream_index][cell_index].upward_flow_in(net, uv_pair)
                    stream_z2.append(z2)
                
                z2_list.append(stream_z2)

            print('this is z2_list: ',z2_list)

            #feeding data to the rule nodes
            z3 = []
            for y_cluster_rule_dict in self.layer3:
                #iterate through each y_stream
                bull_max = 0
                bull_rule = ''
                bear_max = 0
                bear_rule = ''
                for rule_name in y_cluster_rule_dict:
                    #Get the firing strength of each rule 
                    x_clusters = y_cluster_rule_dict[rule_name].x
                    bullbear_of_rule =y_cluster_rule_dict[rule_name].bullbear


                    x_act_arr = []
                    for x_stream in range(len(x_clusters)):
                        x_index = x_clusters[x_stream]
                        x_act_rate = z2_list[x_stream][x_index]
                        x_act_arr.append(x_act_rate)

                    fs = y_cluster_rule_dict[rule_name].get_fs_x(x_act_arr)

                    #comparison with the maximum 
                    if bullbear_of_rule == 'Bull':
                        if fs > bull_max:
                            bull_max = fs
                            bull_rule = rule_name
                    elif bullbear_of_rule == 'Bear':
                        if fs > bear_max:
                            bear_max = fs
                            bear_rule = rule_name

                z3.append([bull_rule, bear_rule])
            print('this is z3_list: ',z3)

            #feeding z3 to z4 to z5 (Done twice because of bull and bear run)
            
            #first do bull predictions 
            z4_bull = []
            for stream in self.layer4:
                for cell_index in range(len(stream)): 
                    m = stream[cell_index].get_mid()
                    rule_cell = self.layer3[cell_index].get(z3[cell_index][0],0)###############
                    if rule_cell != 0:
                        z = rule_cell.fs
                    else:
                        z = 0
                    z4_bull.append([m,z])

            bull_ans = self.layer5[0].defuzzify(z4_bull)

            #second do bear predictions 
            z4_bear = []
            for stream in self.layer4:
                for cell_index in range(len(stream)): 
                    m = stream[cell_index].get_mid()
                    rule_cell = self.layer3[cell_index].get(z3[cell_index][1],0)
                    if rule_cell != 0:
                        z = rule_cell.fs
                        print(rule_cell.label,rule_cell.fs)
                    else:
                        z = 0                    
                    z4_bear.append([m,z])

            bear_ans = self.layer5[0].defuzzify(z4_bear)

            real_ans = y_train[iter][0]
            print( bear_ans,bull_ans, real_ans )



                    
            #Comparison of values
            diff_bear = real_ans - bear_ans
            diff_bull = real_ans - bull_ans

            if math.isnan(diff_bear):
                diff_bear = 10
            if math.isnan(diff_bull):
                diff_bull = 10
            
            #if bull condition wins            
            if abs(diff_bear) > abs(diff_bull):

                if real_ans > bull_ans:
                    magnitude_coeff = min(0.05 * (abs(diff_bull)/0.5), 0.05)
                else:
                    #in between situation
                    diff_ratio = abs(diff_bull) / abs(diff_bear) #range from ~0 to ~1
                    magnitude_coeff = 0.05 * (1/(3*diff_ratio+1))

                momentum_coeff = self.bull_cell.win()
                self.bear_cell.lose()

                bull_bear_change = magnitude_coeff * momentum_coeff 
                self.bullbear_index += bull_bear_change

                if self.bullbear_index > 1 :
                    self.bullbear_index = 1

                print('BULL WINS' , magnitude_coeff , momentum_coeff)

            #if bear condition wins            
            elif abs(diff_bull) > abs(diff_bear):
                if real_ans < bear_ans:
                    magnitude_coeff = min(0.05 * (abs(diff_bear)/0.5), 0.05)
                else:
                    #in between situation
                    diff_ratio = abs(diff_bear) / abs(diff_bull)
                    magnitude_coeff = 0.05 * (1/(3*diff_ratio+1))

                momentum_coeff = self.bear_cell.win()
                self.bull_cell.lose()

                bull_bear_change = magnitude_coeff * momentum_coeff 
                self.bullbear_index  -= bull_bear_change

                if self.bullbear_index < 0 :
                    self.bullbear_index = 0

                print('bear wins' , magnitude_coeff , momentum_coeff)

            print(self.bullbear_index, self.bear_cell.momentum_x, self.bull_cell.momentum_x)

            bb_arr.append(self.bullbear_index)
            real_ans_arr.append(real_ans)

            #BACKPROPAGATION
            
            #train bull
            if bullbear_train[iter] == 1:
                #compute total fs
                z_total = 0
                for mz_pair in z4_bull:
                    z_total += mz_pair[1]
                for stream_index in range(len(z4_bull)):

                    rule_cell = self.layer3[stream_index].get(z3[stream_index][0],0)
                    #create rule cell if it does not exist 
                    if rule_cell ==0:
                         continue
                    #     ans = z3[stream_index][0]
                    #     if ans == '':
                    #         x=1/0
                    #     self.layer3[stream_index][ans] = Rule_cell(label= ans,ip_size =self.ip)
                    #     rule_cell = self.layer3[stream_index].get(ans)
                        #x=input(ans + ' is the rule to be created')

                    z_cur = z4_bull[stream_index][1]
                    m_cur = z4_bull[stream_index][0]
                    z_ratio = z_cur/z_total

                    ideal_ans = real_ans * z_ratio
                    old_ans = m_cur * z_ratio
                    rule_cell.learn(ideal_ans, old_ans,z_total,real_ans)
         
            #train bear
            elif bullbear_train[iter] == 0:
                #compute total fs
                z_total = 0
                for mz_pair in z4_bear:
                    z_total += mz_pair[1]
                for stream_index in range(len(z4_bear)):

                    rule_cell = self.layer3[stream_index].get(z3[stream_index][1],0)
                    #create rule cell if it does not exist 
                    if rule_cell ==0:
                        #  ans = z3[stream_index][1]
                        #  self.layer3[stream_index][ans] = Rule_cell(label= ans,ip_size =self.ip)
                        #  rule_cell = self.layer3[stream_index].get(ans)
                        #x=input(ans + ' is the rule to be created')
                        continue

                    z_cur = z4_bear[stream_index][1]
                    m_cur = z4_bear[stream_index][0]
                    z_ratio = z_cur/z_total

                    ideal_ans = real_ans * z_ratio
                    old_ans = m_cur * z_ratio
                    rule_cell.learn(ideal_ans, old_ans,z_total,real_ans)

            print("backprapogation completed")

                  
            #print space for next line

            iter += 1

            print()


    
        for y_stream in self.layer3:
            for rule in y_stream:
                if y_stream[rule].reliability > 0.1:
                    print(rule, y_stream[rule].reliability)

        #plot the signal data
        bb_signal = train_set[:, -1]
        fig, ax = plt.subplots()
        ax.plot(bb_signal, color ='yellow')
        ax.plot(bb_arr, color ='red')
        
        for x_val in [10, 2990, 3129, 4729, 5121, 5760, 6246, 7748, 8176, 9451, 9523, 12742, 13367, 14529, 14577] :
            ax.axvline(x=x_val)

        ax.set_xlabel('days')
        ax.set_ylabel('BB_signal',color = 'red')

        #to plot the main graph
        ax2=ax.twinx()
        train_set = np.genfromtxt(original_add, delimiter = '\t', skip_header=6)
        series = train_set[:,0]

        ax2.plot(series,color = 'orange')
        ax2.set_ylabel('Actual Price',color = 'orange')
        plt.savefig('train_results.png')
        plt.show()

        # testing to see how well it matches the train sets

        #self.test(bullbear_test_set, bb_signal)
        
    
    def test(self, test_set,original_add):
        print()
        print("=================================This is the testing phase ====================================")
        print()

        smoothen_factor= 20

        bb_arr =[]
        real_ans_arr = []

        x_test = test_set[:, :-(self.op)]
        y_test = test_set[:, self.ip:]


        limit = len(y_test)
        iter = 20
        while  iter < limit:
            print(iter)

            #feeding data to LAYER ONE 
            z1_list = []
            x_list = []
            for ip_num in range(len(self.layer1)):
                x_smoo = sum(x_test[iter-smoothen_factor:iter, ip_num])/smoothen_factor
                uv_list,z = self.layer1[ip_num].upward_flow_in(x_smoo)
                z1_list += [uv_list]
                x_list += [z]
            
            print('this is x: ',x_list)
            print('this is z1:',z1_list) #to see how data is passed from layer 1 to layer 2.

            #feedin data to LAYER TWO 
            z2_list = []
            #iterate through the stream
            for stream_index in range(len(z1_list)):
                stream = z1_list[stream_index]
                net = x_list[stream_index]

                #data flow in to LAYER TWO cells
                stream_z2 = []
                for cell_index in range(len(stream)):
                    uv_pair = stream[cell_index]
                    z2 = self.layer2[stream_index][cell_index].upward_flow_in(net, uv_pair)
                    stream_z2.append(z2)
                
                z2_list.append(stream_z2)

            print('this is z2_list: ',z2_list)

            #feeding data to the rule nodes
            z3 = []
            for y_cluster_rule_dict in self.layer3:
                #iterate through each y_stream
                bull_max = 0
                bull_rule = ''
                bear_max = 0
                bear_rule = ''
                for rule_name in y_cluster_rule_dict:
                    #Get the firing strength of each rule 
                    x_clusters = y_cluster_rule_dict[rule_name].x
                    bullbear_of_rule =y_cluster_rule_dict[rule_name].bullbear


                    x_act_arr = []
                    for x_stream in range(len(x_clusters)):
                        x_index = x_clusters[x_stream]
                        x_act_rate = z2_list[x_stream][x_index]
                        x_act_arr.append(x_act_rate)

                    fs = y_cluster_rule_dict[rule_name].get_fs_x(x_act_arr)

                    #comparison with the maximum 
                    if bullbear_of_rule == 'Bull':
                        if fs > bull_max:
                            bull_max = fs
                            bull_rule = rule_name
                    elif bullbear_of_rule == 'Bear':
                        if fs > bear_max:
                            bear_max = fs
                            bear_rule = rule_name

                z3.append([bull_rule, bear_rule])
            print('this is z3_list: ',z3)

            #feeding z3 to z4 to z5 (Done twice because of bull and bear run)
            
            #first do bull predictions 
            z4_bull = []
            for stream in self.layer4:
                for cell_index in range(len(stream)): 
                    m = stream[cell_index].get_mid()
                    rule_cell = self.layer3[cell_index].get(z3[cell_index][0],0)###############
                    if rule_cell != 0:
                        z = rule_cell.fs
                    else:
                        z = 0
                    z4_bull.append([m,z])

            bull_ans = self.layer5[0].defuzzify(z4_bull)

            #second do bear predictions 
            z4_bear = []
            for stream in self.layer4:
                for cell_index in range(len(stream)): 
                    m = stream[cell_index].get_mid()
                    rule_cell = self.layer3[cell_index].get(z3[cell_index][1],0)
                    if rule_cell != 0:
                        z = rule_cell.fs
                        print(rule_cell.label,rule_cell.fs)
                    else:
                        z = 0                    
                    z4_bear.append([m,z])

            bear_ans = self.layer5[0].defuzzify(z4_bear)

            real_ans = sum(y_test[iter-smoothen_factor:iter, 0])/smoothen_factor

            print( bear_ans,bull_ans, real_ans )

           #Comparison of values
            diff_bear = real_ans - bear_ans
            diff_bull = real_ans - bull_ans

            if math.isnan(diff_bear):
                diff_bear = 10
            if math.isnan(diff_bull):
                diff_bull = 10
            
            #if bull condition wins            
            if abs(diff_bear) > abs(diff_bull):

                if real_ans > bull_ans:
                    magnitude_coeff = min(0.05 * (abs(diff_bull)/0.5), 0.05)
                else:
                    #in between situation
                    diff_ratio = abs(diff_bull) / abs(diff_bear) #range from ~0 to ~1
                    magnitude_coeff = 0.05 * (1/(3*diff_ratio+1))

                momentum_coeff = self.bull_cell.win()
                self.bear_cell.lose()

                bull_bear_change = magnitude_coeff * momentum_coeff 
                self.bullbear_index += bull_bear_change

                if self.bullbear_index > 1 :
                    self.bullbear_index = 1

                print('BULL WINS' , magnitude_coeff , momentum_coeff)

            #if bear condition wins            
            elif abs(diff_bull) > abs(diff_bear):
                if real_ans < bear_ans:
                    magnitude_coeff = min(0.05 * (abs(diff_bear)/0.5), 0.05)
                else:
                    #in between situation
                    diff_ratio = abs(diff_bear) / abs(diff_bull)
                    magnitude_coeff = 0.05 * (1/(3*diff_ratio+1))

                momentum_coeff = self.bear_cell.win()
                self.bull_cell.lose()

                bull_bear_change = magnitude_coeff * momentum_coeff 
                self.bullbear_index  -= bull_bear_change

                if self.bullbear_index < 0 :
                    self.bullbear_index = 0

                print('bear wins' , magnitude_coeff , momentum_coeff)

            print(self.bullbear_index, self.bear_cell.momentum_x, self.bull_cell.momentum_x)

            bb_arr.append(self.bullbear_index)



            print("")
            iter += 1
        
        print(bb_arr)
        
        #plot the signal data
        fig, ax = plt.subplots()

        ax.plot([x for x in range(smoothen_factor,limit)],bb_arr, color ='red')
        

        ax.set_xlabel('days')
        ax.set_ylabel('BB_signal',color = 'red')

        #to plot the main graph
        ax2=ax.twinx()
        train_set = np.genfromtxt(original_add, delimiter = '\t', skip_header=6)
        series = train_set[:,0]

        ax2.plot(series,color = 'orange')
        ax2.set_ylabel('Actual Price',color = 'orange')
        plt.savefig('test_results.png')
        plt.show()

    def visualise(self):
        graph = Digraph(comment='CLS-Visualisation', format='png',
            graph_attr=dict(ranksep='1.4', rankdir='BT', color='white', splines='line'),
            node_attr= dict(shape='circle',width='1'))

        layer = '1'
        connector = '-'

        layer1_cell_names = []
        layer5_cell_names = []

        #plot layer 1
        with graph.subgraph(name=f'l1') as first:
            first.attr(label= 'input')
            first.node_attr.update(width='3')
            first.graph_attr.update(fontsize ='50')            
            for node in self.layer1:
                cell_name =layer+connector+str(node.stream)
                first.node(cell_name,cell_name )
                layer1_cell_names.append(cell_name)

        layer='2'
        #plot layer 2
        with graph.subgraph(name=f'l2') as second:
            second.attr(label= 'input_cluster')
            for stream_index in range(len(self.layer2)):
                cluster_index=0
                layer1_cell_name = layer1_cell_names[stream_index]
                for node in self.layer2[stream_index]:
                    cell_name =layer+connector+str(stream_index)+connector+str(cluster_index)
                    second.node(cell_name,cell_name )
                    graph.edge(layer1_cell_name ,cell_name)
                    cluster_index+=1
        
        layer = '3'
        with graph.subgraph(name=f'l3') as third:
            third.node_attr.update(shape='rectangle', width='30',height='6')
            third.node('RULES', 'RULES')


        layer='4'
        #plot layer 4
        with graph.subgraph(name=f'l4') as fourth:
            fourth.attr(label= 'output_cluster')
            for stream_index in range(len(self.layer4)):
                cluster_index=0
                for node in self.layer4[stream_index]:
                    cell_name =layer+connector+str(stream_index)+connector+str(cluster_index)
                    fourth.node(cell_name,cell_name )
                    cluster_index+=1

        #plot layer 5
        layer = '5'
        with graph.subgraph(name=f'l5') as fifth:
            fifth.attr(label= 'output')
            fifth.node_attr.update(width='3')
            fifth.graph_attr.update(fontsize ='50')            

            for node in self.layer5:
                cell_name =layer+connector+str(node.stream)
                fifth.node(cell_name,cell_name )
                layer5_cell_names.append(cell_name)
        
        #plot layer 4&5 edge
        layer = '4'
        for stream_index in range(len(self.layer4)):
            cluster_index=0
            layer5_cell_name = layer5_cell_names[stream_index]
            for node in self.layer4[stream_index]:
                cell_name =layer+connector+str(stream_index)+connector+str(cluster_index)

                graph.edge(cell_name,layer5_cell_name )
                cluster_index+=1

        #plot layer 2&3 edge
        layer='2'
        for stream_index in range(len(self.layer2)):
            cluster_index=0
            layer1_cell_name = layer1_cell_names[stream_index]
            for node in self.layer2[stream_index]:
                cell_name =layer+connector+str(stream_index)+connector+str(cluster_index)
                graph.edge(cell_name ,'RULES')
                cluster_index+=1

        #plot layer 3&4 edge
        layer='4'
        for stream_index in range(len(self.layer4)):
            cluster_index=0
            for node in self.layer4[stream_index]:
                cell_name =layer+connector+str(stream_index)+connector+str(cluster_index)
                graph.edge('RULES',cell_name )
                cluster_index += 1

       
        # #print(graph.source)
        g = graph.unflatten(stagger = 2)
        g.render('visualisation.gv', view= False)
