#import numpy as np
import math
import gurobipy as gp
import data as d, optimizationModel as om
import plot
from collections import defaultdict

class Model:
    
    # ================== INITIALIZATION ==================
    
    def __init__(self):
        print(d.time_periods)
        self.multiplier = d.number_of_time_periods_per_hour
        self.nodes = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: False)))
        for vessel in d.vessels:
            self.nodes[vessel.number][16*self.multiplier][0] = True
        self.fuel_cost = [[[[[0 for end_time in d.time_periods] for destinatintion_order in d.orders] for start_time in d.time_periods] for departure_order in d.orders] for vessel in d.vessels]

    # self.fuel_cost[vessel][departure_order][start_node_time][destination_order][finish_node_time]
        self.counter = 0;
        self.name = "testrun"
        self.run_model()




    # ================== RUNNING THE MODEL ==================
    
    def run_model(self):


        
        print("\n\n================== INITIALIZING MODEL ==================\n")
        self.build_model()
        print("\nNetwork generation successful!")
        print("------------------------------------------------")
        
#       ------------------------------------------------------------
#       | OBS! Comment out graph plotting function when optimizing |
#       ------------------------------------------------------------
        
        print("Plotting graph....")
        # plot.draw_routes(self.fuel_cost)
        
        print("-------------- OPTIMIZING MODEL ----------------\n")

        om.solve(self.fuel_cost, self.name)
        """
        except gp.GurobiError as e:
            print('Error code ' + str(e.errno) + ": " + str(e))
        
        except AttributeError:
            print('Encountered an attribute error')
        """
        
        
        
    # ================== BUILDING THE NETWORK ==================

    
    # ------------------ Deciding what nodes to sail from ------------------
    
    def build_model(self): #TODO fix so that arcs are created to and from depot aswell

        print(self.nodes)

        for vessel in d.vessels:
            
            for time in range(16*self.multiplier, vessel.return_day*24*self.multiplier):

                for order in d.orders:

                    if self.nodes[vessel.number][time][order.number]:
                        self.build_arcs(vessel.number, time, order)
        
    
    
    
    # ------------------ Deciding what nodes to sail to ------------------
    
    def build_arcs(self, vessel_number, start_node_time, departure_order):
        
        for destination_order in d.orders:
            
            if destination_order.number != departure_order.number:

                departure_installation_number = departure_order.installation.number
                destination_installation_number = destination_order.installation.number

                distance = d.get_distance_between_installation_number(departure_installation_number, destination_installation_number)

                real_start_time = self.convert_from_node_time_to_real_time(start_node_time)

                earliest_theoretical_end_time = start_node_time + math.ceil((distance/d.max_speed + destination_order.demand * d.time_spent_per_demand_unit) * self.multiplier)
                latest_theoretical_end_time = start_node_time + math.ceil((distance/d.min_speed + destination_order.demand * d.time_spent_per_demand_unit) * self.multiplier)

                fin_servicing_time = earliest_theoretical_end_time

                while fin_servicing_time <= latest_theoretical_end_time:


                    fin_servicing_time = self.get_earliest_feasible_fin_servicing_time(fin_servicing_time, destination_order, 0)

                    servicing_consumption, real_fin_idling_time = self.servicing_calculations(fin_servicing_time, destination_order)

                    if self.is_arrival_possible(real_start_time, distance, real_fin_idling_time) != True:
                        fin_servicing_time += 1
                        continue

                    idling_consumption, real_fin_sailing_time = self.idling_calculatiuons(real_start_time, distance, real_fin_idling_time)

                    sailing_consumption = 0

                    if distance != 0:
                        time_in_all_weather_states = self.get_time_in_all_WS(real_start_time, real_fin_sailing_time)
                        adjusted_average_speed = self.calculate_adjusted_average_speed(time_in_all_weather_states, distance)
                        sailing_consumption = self.sailing_calculations(time_in_all_weather_states, adjusted_average_speed)

                    self.add_arc(vessel_number, departure_order, destination_order, start_node_time, fin_servicing_time, sailing_consumption, idling_consumption, servicing_consumption)
                    self.counter += 1

                    fin_servicing_time += 1

   
    # ------------------ Adding arcs to the model ------------------
    
    def add_arc(self, vessel_number, departure_order, destination_order, start_node_time, finish_node_time, sailing_consumption, idling_consumption, servicing_consumption):

        vessel = d.get_vessel_by_number(vessel_number)

        if finish_node_time < vessel.return_day * 24 * self.multiplier:

            self.nodes[vessel_number][finish_node_time][destination_order.number] = True

            print()
            print("Adding arc number:", self.counter)
            print("vessel:",vessel_number,"dep order: ", departure_order.number, "dest order: ", destination_order.number, "start: ", start_node_time,"finish: ", finish_node_time, "c sail: ", sailing_consumption, "c idle: ", idling_consumption, "c ser: ", servicing_consumption)

            self.fuel_cost[vessel_number][departure_order.number][start_node_time][destination_order.number][finish_node_time] = ((sailing_consumption + idling_consumption + servicing_consumption)*d.fuel_price)
        else:
            self.counter -= 1
    
    # ================== HELPING FUNCTIONS ==================    

    def get_distance_between_installations(self, installation_1, installation_2):
        return self.Distance[installation_1][installation_2]

    def convert_from_node_time_to_real_time(self, time):
        return time/self.multiplier

    def convert_from_real_time_to_node_time(self, time):
        return round(time*self.multiplier)

    def get_earliest_feasible_fin_servicing_time(self, fin_servicing_time, destination_order, iteration_number):
        erliest_feasible_fin_servicing_time = fin_servicing_time
        if not self.is_servicing_possible(fin_servicing_time, destination_order):
            erliest_feasible_fin_servicing_time = self.get_earliest_feasible_fin_servicing_time(erliest_feasible_fin_servicing_time +1, destination_order, iteration_number +1)
        return erliest_feasible_fin_servicing_time

    def servicing_calculations(self, fin_servicing_time, destination_order):
        real_time = self.convert_from_node_time_to_real_time(fin_servicing_time)
        servicing_time_left = destination_order.demand * d.time_spent_per_demand_unit
        consumtion = 0
        while servicing_time_left > 0:
            if real_time % 1 > 0:
                if servicing_time_left < (real_time % 1) / d.get_weather_impact(real_time):
                    consumtion += d.fuel_consumption_DP * servicing_time_left * d.get_weather_impact(real_time)
                    real_time -= servicing_time_left * d.get_weather_impact(real_time)
                    servicing_time_left = -1
                else:
                    consumtion += d.fuel_consumption_DP * (real_time % 1) * d.get_weather_impact(real_time)
                    servicing_time_left -= (real_time % 1) / d.get_weather_impact(real_time)
                    real_time = math.floor(real_time)
            else:
                if servicing_time_left < 1 / d.get_weather_impact(real_time - 1):
                    consumtion += d.fuel_consumption_DP * servicing_time_left * d.get_weather_impact(real_time - 1)
                    real_time -= servicing_time_left * d.get_weather_impact(real_time - 1)
                    servicing_time_left = -1
                else:
                    consumtion += d.fuel_consumption_DP * d.get_weather_impact(real_time - 1)
                    servicing_time_left -= 1 / d.get_weather_impact(real_time - 1)
                    real_time -= 1
        return consumtion, real_time


    def is_servicing_possible(self, fin_servicing_time, destination_order):
        real_time = self.convert_from_node_time_to_real_time(fin_servicing_time)
        servicing_time_left = destination_order.demand * d.time_spent_per_demand_unit
        while servicing_time_left > 0:
            if d.get_weather_state(real_time) == 3 or d.is_installation_by_order_number_closed(destination_order, real_time):
                return False
            elif real_time % 1 > 0:
                if servicing_time_left < (real_time % 1) / d.get_weather_impact(real_time):
                    return True
                else:
                    servicing_time_left -= (real_time % 1) / d.get_weather_impact(real_time)
                    real_time = math.floor(real_time)
            else:
                if servicing_time_left < 1 / d.get_weather_impact(real_time - 1):
                    return True
                else:
                    servicing_time_left -= 1 / d.get_weather_impact(real_time - 1)
                    real_time -= 1
        return True

    def is_arrival_possible(self, real_start_time, distance, real_fin_idling_time):
        time_in_weather_states = self.get_time_in_all_WS(real_start_time, real_fin_idling_time)
        max_distance = time_in_weather_states[0]* d.max_speed + time_in_weather_states[1]*d.max_speed + time_in_weather_states[2]*(d.max_speed - 2) + time_in_weather_states[3] * (d.max_speed - 3)
        if max_distance >= distance:
            return True
        return False

    def idling_calculatiuons(self, real_start_time, distance, real_fin_idling_time):
        longest_sailing_time = distance/d.max_speed
        if (longest_sailing_time >= real_fin_idling_time - real_start_time):
            return 0, real_fin_idling_time
        else:
            idling_duration = real_fin_idling_time - longest_sailing_time - real_start_time
            real_fin_sailing_time = real_fin_idling_time - idling_duration
            time_in_weather_states = self.get_time_in_all_WS(real_fin_sailing_time, real_fin_idling_time)
            idling_consumption = 0
            for i in range(4):
                idling_consumption += time_in_weather_states[i] * d.SpeedImpact[i] * d.fuel_consumption_idling
            return idling_consumption, real_fin_sailing_time

    def get_time_in_all_WS(self, t1, t2):
        tiws3 = self.get_time_in_WS(t1, t2, 3)
        tiws2 = self.get_time_in_WS(t1, t2, 2)
        tiws1 = self.get_time_in_WS(t1, t2, 1)
        tiws0 = t2 - t1 - tiws1 - tiws2 - tiws3
        return [tiws0, tiws1, tiws2, tiws3]


    def get_time_in_WS(self, t1, t2, weather_state):
        time = 0
        _t1 = t1
        while _t1 < t2:
            if _t1 % 1 > 0:
                if t2 - _t1 <= 1 - (_t1 % 1):
                    time += t2 - _t1 if self.is_weather_state(weather_state, _t1) else 0
                    _t1 = t2 + 1
                else:
                    time += 1 - (_t1 % 1) if self.is_weather_state(weather_state, _t1) else 0
                    _t1 = math.ceil(_t1)
            else:
                if t2 - _t1 <= 1:
                    time += t2 - _t1 if self.is_weather_state(weather_state, _t1) else 0
                    _t1 = t2 + 1
                else:
                    time += 1 if self.is_weather_state(weather_state, _t1) else 0
                    _t1 += 1
        return time


    def is_weather_state(self, weather_state, time):
        return d.get_weather_state(time) == weather_state

    def calculate_adjusted_average_speed(self, time_in_all_weather_states, distance):
        durationWS3 = time_in_all_weather_states[3]
        durationWS2 = time_in_all_weather_states[2]
        durationWS01 = time_in_all_weather_states[1] + time_in_all_weather_states[0]
        duration = sum(time_in_all_weather_states)
        speed = distance / duration
        if durationWS01 == 0 and speed > (durationWS2 * (d.max_speed - 2) + durationWS3 * (d.max_speed - 3))/(durationWS2 + durationWS3):
            speed = d.max_speed + 1
        else:
            if speed > (d.max_speed - 3):
                speed += (durationWS3 * (speed - (d.max_speed - 3))) / (durationWS01 + durationWS2)
            if speed > (d.max_speed - 2):
                speed += (durationWS2 * (speed - (d.max_speed - 2))) / durationWS01
        return speed

    def sailing_calculations(self, time_in_all_weather_states, adjusted_average_speed):
        cost = 0
        cost += (time_in_all_weather_states[0] + time_in_all_weather_states[1]) * self.consumptionFunction(adjusted_average_speed)
        cost += time_in_all_weather_states[2] * self.consumptionFunction(adjusted_average_speed + 2) if adjusted_average_speed < d.max_speed - 2 else time_in_all_weather_states[2] * self.consumptionFunction(d.max_speed)
        cost += time_in_all_weather_states[3] * self.consumptionFunction(adjusted_average_speed + 3) if adjusted_average_speed < d.max_speed - 3 else time_in_all_weather_states[3] * self.consumptionFunction(d.max_speed)
        return cost

    def consumptionFunction(self, speed):
        return (11.111 * speed * speed - 177.78 * speed + 1011.1)


    #TODO! inject some juicy spot price

        