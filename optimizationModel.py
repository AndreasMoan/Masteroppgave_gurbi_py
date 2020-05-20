import gurobipy as gp
import data as d



def solve(fuel_cost, Name):

    # =============== INITIATE MODEL ===============
    
    Env = gp.Env(Name + ".log")
    
    model = gp.Model(name = Name, env = Env)
    
    model.setParam('TimeLimit', 3*60*60)
    
    # =============== SETS ===============


    
    # --------------- node_times ---------------
    
    node_times = [[[]for i in d.order_numbers]for v in d.vessel_numbers]

    for v in d.vessel_numbers:
        for i in d.order_numbers:
            for t in d.time_periods:
                count = 0
                for j in d.order_numbers:
                    for tau in d.time_periods:
                        if fuel_cost[v][j][tau][i][t] != 0 or fuel_cost[v][i][t][j][tau] != 0:
                            count += 1
                if count != 0:
                    node_times[v][i].append(t)



    # --------------- node_vessels ---------------

    node_vessels = [[[]for t in d.time_periods] for i in d.order_numbers]

    for i in d.order_numbers:
        for t in d.time_periods:
            for v in d.vessel_numbers:
                count = 0
                for j in d.order_numbers:
                    for tau in d.time_periods:
                        if fuel_cost[v][j][tau][i][t] != 0 or fuel_cost[v][i][t][j][tau] != 0:
                            count += 1
                if count != 0:
                    node_vessels[i][t].append(v)



    # --------------- to_insts ---------------

    to_insts = [[[[]for t in d.time_periods]for i in d.order_numbers]for v in d.vessel_numbers] # tror denne er riktig

    for v in d.vessel_numbers:
        for i in d.order_numbers:
            for t in node_times[v][i]:
                for j in d.order_numbers:
                    count = 0
                    for tau in d.time_periods:
                        if fuel_cost[v][i][t][j][tau] != 0:
                            count += 1
                    if count > 0:
                        to_insts[v][i][t].append(j)



    # --------------- from_insts ---------------

    from_insts = [[[[]for tau in d.time_periods]for j in d.order_numbers]for v in d.vessel_numbers]

    for v in d.vessel_numbers:
        for j in d.order_numbers:
            for tau in node_times[v][j]:
                for i in d.order_numbers:
                    count = 0
                    for t in d.time_periods:
                        if fuel_cost[v][i][t][j][tau] != 0:
                            count += 1
                    if count > 0:
                        from_insts[v][j][tau].append(i)



    # --------------- departure_times ---------------

    departure_times = [[[[]for j in d.order_numbers] for i in d.order_numbers] for v in d.vessel_numbers]    #ser riktig ut

    for v in d.vessel_numbers:
        for i in d.order_numbers:
            for j in d.order_numbers:
                for t in d.time_periods:
                    count = 0
                    for tau in d.time_periods:                                           #kan evt skrive for tau større enn t (for å øke leseligheten)
                        if fuel_cost[v][i][t][j][tau] != 0:
                            count += 1
                    if count != 0:
                        departure_times[v][i][j].append(t)



    # --------------- arrival_times ---------------

    arrival_times = [[[[]for j in d.order_numbers] for i in d.order_numbers] for v in d.vessel_numbers]

    for v in d.vessel_numbers:
        for i in d.order_numbers:
            for j in d.order_numbers:
                for tau in d.time_periods:
                    count = 0
                    for t in d.time_periods:
                        if fuel_cost[v][i][t][j][tau] != 0:
                            count += 1
                    if count != 0:
                        arrival_times[v][i][j].append(tau)



    # --------------- specific_departure_times ---------------

    specific_departure_times = [[[[[] for tau in d.time_periods] for j in d.order_numbers] for i in d.order_numbers] for v in d.vessel_numbers]

    for v in d.vessel_numbers:
        for i in d.order_numbers:
            for j in d.order_numbers:
                for tau in arrival_times[v][i][j]:
                    for t in d.time_periods:
                        if fuel_cost[v][i][t][j][tau] != 0:
                            specific_departure_times[v][i][j][tau].append(t)



    # --------------- specific_arrival_times ---------------

    specific_arrival_times = [[[[[] for j in d.order_numbers] for t in d.time_periods] for i in d.order_numbers] for v in d.vessel_numbers]

    for v in d.vessel_numbers:
        for i in d.order_numbers:
            for j in d.order_numbers:
                for t in departure_times[v][i][j]:
                    for tau in d.time_periods:
                        if fuel_cost[v][i][t][j][tau] != 0:
                            specific_arrival_times[v][i][t][j].append(tau)



    # --------------- symmetric_vessels ---------------

    # =============== PARAMETERS ===============


    # =============== VARIABLES ===============

    x = {}

    for v in d.vessel_numbers:
        for i in d.order_numbers:
            for j in d.order_numbers:
                if j != i:
                    for t in departure_times[v][i][j]:
                        for tau in specific_arrival_times[v][i][t][j]:
                           x[v,i,t,j,tau] = model.addVar(vtype=gp.GRB.BINARY, name=("x_" + str(v) + "_" + str(i) + "_" + str(t) + "_" + str(j) + "_" + str(tau)))


#    a = [[0 for tau in Times]for j in Insts]
#
#    for j in Insts:
#        for tau in Times:
#            a[j][tau] = model.addVar(vtype=gp.GRB.INTEGER, name=("a_" + str(j) + "_" + str(tau)))


#            print("\rGenerating variables: %d%% "%math.ceil(counter*100/(np.size(Vessels)*np.size(Insts))), end="\r", flush = True)
#            counter += 1



    # =============== MODEL UPDATE ===============

    model.update()



    # =============== CONSTRAINTS ===============


    # --------------- Flow conservation ---------------

    model.addConstrs((

            gp.quicksum(

                    x[v,j,tau,i,t]

                    for j in from_insts[v][i][t]
                    for tau in specific_departure_times[v][j][i][t])

            - gp.quicksum(

                    x[v,i,t,j,tau]

                    for j in to_insts[v][i][t]
                    for tau in specific_arrival_times[v][i][t][j])

            == 0

            for v in d.vessel_numbers
            for i in d.order_numbers
            if i != 0
            for t in node_times[v][i])

            , "Flow_Conservation:_v" + str(v) + " i" + str(i) + " t" + str(t))



    # --------------- Any installation can only be visited once per voyage ---------------

    model.addConstrs((

            gp.quicksum(

                    x[v,i,t,j,tau]

                    for i in d.order_numbers
                    if i != j
                    for t in departure_times[v][i][j]
                    for tau in specific_arrival_times[v][i][t][j])

            <= 1

            for j in d.order_numbers
            for v in d.vessel_numbers)

            , "Only one Inst visit per voy: j" + str(j) + " v" + str(v))



    # --------------- Evry PSV can only sail from the depot once per voyage ---------------

    model.addConstrs((

            gp.quicksum(

                    x[v,0,t,j,tau]

                    for j in d.order_numbers
                    for t in departure_times[v][0][j]
                    for tau in specific_arrival_times[v][0][t][j])

            <= 1

            for v in d.vessel_numbers)

            , "Only sail from depot once per voyage: v" + str(v))





    # --------------- All service jobs must be performed ---------------

    model.addConstrs((

            gp.quicksum(

                    x[v,i,t,j,tau]

                    for v in d.vessel_numbers
                    for i in d.order_numbers
                    if i != j
                    for t in departure_times[v][i][j]
                    for tau in specific_arrival_times[v][i][t][j])

            == 1

            for j in d.order_numbers
            if j != 0)

            , name = ("Demanded visits: j" + str(j)))



    # --------------- PSV capacity ---------------


    model.addConstrs((

            gp.quicksum(

                    x[v,i,t,j,tau] * d.orders[j].demand

                    for i in d.order_numbers
                    for j in d.order_numbers
                    if j != 0
                    for t in departure_times[v][i][j]
                    for tau in specific_arrival_times[v][i][t][j])

            <= d.vessels[v].capacity

            for v in d.vessel_numbers)

            , "PSV capacity: v" + str(v))


    # =============== MODEL UPDATE ===============

    model.update()


    # =============== OBJECTIVE ===============

    model.setObjective(

            gp.quicksum(x[v,i,t,j,tau] * fuel_cost[v][i][t][j][tau]
                for v in d.vessel_numbers
                for i in d.order_numbers
                for j in d.order_numbers 
                if j != i
                for t in departure_times[v][i][j]
                for tau in specific_arrival_times[v][i][t][j]), 
            
            gp.GRB.MINIMIZE)
                        
        
            
    # =============== MODEL UPDATE ===============

    model.update()
    
    model.printStats()
    
    model.write(Name + ".lp")

    # =============== RUN MODEL ===============
    
    model.optimize()
    
    model.printAttr('x')
    


    #plotSol.draw_routes(solEdges, fuel _cost)

