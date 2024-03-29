#----------------------------------------- Importing Libraries -----------------------------------------

import random
import datetime
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import style
from collections import Counter
from prettytable import PrettyTable
from deap import algorithms, base, tools, creator
style.use('ggplot')

#-------------------------------------------- Reading Data ---------------------------------------------

# Reading CSV file
df = pd.read_csv('Gudur_Rythu_Bazar_2017.csv')
df.drop(['Comments'], axis = 1, inplace=True)	#Dropping 'Comments' column

# np arrays of colomns
Harvest_time = df['Maturity_mo']
Harvest_time = np.array(Harvest_time)
Month = df['Month']
Month = np.array(Month)
Crop_name = df['Type']
Crop_name = np.array(Crop_name)
Profit = df['Profit']
Profit = np.array(Profit)
Culti_cost = df['Cost_Culti_acre']
Culti_cost = np.array(Culti_cost)
Type = df['Type_Code']
Type = np.array(Type)
Root_depth = df['Root_Depth']
Root_depth = np.array(Root_depth)
Water_req = df['Water_Req']
Water_req = np.array(Water_req)

Current_month = datetime.datetime.now().month
Current_month = 5
Current_month_str = datetime.datetime.today().strftime('%B')
Debug = False
Max_=[]
Avg_=[]
Std_=[]
profit_wt = 0.7
risk_wt = -0.3
root_risk_wt = 0.5
water_risk_wt = 0.5
n_i = 1		#Lower limit of no.of crops
n_f = 20	#Upper limit of no.of crops / Total no.of crops
m = 6		#No.of crops to decide

#--------------------------------------------------------------------------------------------------------

# Outputs list of harvest months
def Harvest_month(code_val):

	harvest_month=[]
	for i in range(12):
		if (i+1)*(Harvest_time[(code_val-1)*12]+1) <= 12: 
			crop_id = (code_val-1)*12 + Harvest_time[(code_val-1)*12] + (Current_month -1) + \
			i*(Harvest_time[(code_val-1)*12]+1)		#continuation
			crop_id_verify = Harvest_time[(code_val-1)*12] + (Current_month -1) + i*(Harvest_time[(code_val-1)*12]+1)
			if crop_id_verify < 12:
				crop_id = crop_id
				harvest_month.append(Month[crop_id])
				# break
			else :
				crop_id = (code_val-1)*12 + crop_id%12
				harvest_month.append(Month[crop_id])
				# break
		else:
			break
	return harvest_month

# Outputs list of planting months
def Planting_month(code_val):

	planting_month=[]
	for i in range(12):
		if (i+1)*(Harvest_time[(code_val-1)*12]+1) <= 12: 
			crop_id = (code_val-1)*12 + (Current_month -1) + i*(Harvest_time[(code_val-1)*12]+1)
			crop_id_verify = (Current_month -1) + i*(Harvest_time[(code_val-1)*12]+1)
			if crop_id_verify < 12:
				crop_id = crop_id
				planting_month.append(Month[crop_id])
				# break
			else :
				crop_id = (code_val-1)*12 + crop_id%12
				planting_month.append(Month[crop_id])
				# break
		else:
			break
	return planting_month

# Total profit of each individual 
# Objective fun : Sum of profits of 'm' crops
# Subject to constrains : [1] Harvest time.
#						  [2] Crop cycle in a year based on harvest time.
#						  [3] Based on root system.
#						  [4] Based on water requirement.
def Fitness_value(individual):

	global profit
	profit = []
	root_depth = []
	water_req = []

	#---------------------------------------------- Estimating Profit -----------------------------------------

	if len(set(individual))==m:
		for i in range(len(individual)):
			profit_itt = []
			Crop = individual[i]
			for e in range(len(Type)):
				if Type[e]==Crop:
					type_id = e
					break
				else:
					pass

			for i in range(12):
				if (i+1)*(Harvest_time[type_id]+1) <= 12: 

					profit_id = type_id + Current_month + Harvest_time[type_id] -1 + i*(Harvest_time[type_id]+1)
					id_verify = Current_month + Harvest_time[type_id] -1 + i*(Harvest_time[type_id]+1)
					if id_verify < 12:
						profit_i = Profit[profit_id]
						profit_itt.append(profit_i)
						# break
					else:
						profit_i = Profit[type_id + profit_id%12]
						profit_itt.append(profit_i)
						# break
				else:
					break
			profit.append(sum(profit_itt))
			root_depth.append(Root_depth[type_id])
			water_req.append(Water_req[type_id])

	else:
		profit=[0]
	# print(sum(profit))
	Profit_percent = sum(profit)/10**4

	#---------------------------------------------- Estimating Risk -------------------------------------------

	list_risk=[]

	# Risk due to competition over nitrogen from the soil
	# lower limit = 0
	# upper limit = 100
	list_abc_1=[]
	counts = Counter(root_depth)
	per_s = counts['Shallow']*100/m
	per_m = counts['Medium']*100/m
	per_d = counts['Deep']*100/m
	
	if per_s and per_m != 0:
		a_1 = abs(per_s - per_m)
		list_abc_1.append(a_1)
	if per_s and per_d != 0:
		b_1 = abs(per_s - per_d)
		list_abc_1.append(b_1)
	if per_m and per_d != 0:
		c_1 = abs(per_m - per_d)
		list_abc_1.append(c_1)
	if len(list_abc_1) != 0:
		avg_abc_1 = sum(list_abc_1)/len(list_abc_1)
	else:
		avg_abc_1 = 100
	list_risk.append(avg_abc_1)

	# Risk due to competition over water requirement
	# lower limit = m*20
	# upper limit = m*50
	list_abc_2=[]
	counts_water = Counter(water_req)
	per_L = counts_water['L']
	per_M = counts_water['M']
	per_H = counts_water['H']
	
	avg_abc_2 = 20*per_L + 30*per_M + 50*per_H

	list_risk.append(avg_abc_2)
	
	# risk = (root_risk_wt*list_risk[0] + water_risk_wt*list_risk[1])/(root_risk_wt + water_risk_wt)
	risk = (root_risk_wt*list_risk[0] + water_risk_wt*list_risk[1])
	Risk_percent = risk

	#-----------------------------------------------------------------------------------------------------------
	
	# combined_val = (profit_wt*Profit_percent+risk_wt*Risk_percent)/(profit_wt+risk_wt)
	combined_val = (profit_wt*Profit_percent+risk_wt*Risk_percent)
	
	if Debug == True:
		print('-- Debugging --')
		print('Profit_val 	: %s \nRisk_val 	: %s \nCombined_val 	: %s \nRisk_root 	: %s \nRisk_water 	: %s' \
			%(Profit_percent, Risk_percent, combined_val, avg_abc_1, avg_abc_2) )
	else:
		pass

	# return sum(profit), risk
	return combined_val, 

# ----------------------------------------- Creating class --------------------------------------------------

# creator.create('FitnessMax', base.Fitness, weights = (1.0, -1.0))
creator.create('FitnessMax', base.Fitness, weights = (1.0, ))
creator.create('Individual', list, fitness = creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register('attr_value', random.randint, n_i, n_f)	#generator
# Structure initializers
toolbox.register('individual', tools.initRepeat, creator.Individual, toolbox.attr_value, m)	
toolbox.register('population', tools.initRepeat, list, toolbox.individual)
# genetic operators required for the evolution
toolbox.register('evaluate', Fitness_value)
toolbox.register('mate', tools.cxTwoPoint)
toolbox.register('mutate', tools.mutUniformInt, low=n_i, up=n_f, indpb=0.2)
toolbox.register('select', tools.selTournament, tournsize=3)

#------------------------------------------ Evolution operation ----------------------------------------------

def main():

	# create an initial population of 300 individuals
	pop = toolbox.population(n=300)
	# CXPB  is the probability with which two individuals are crossed
	# MUTPB is the probability for mutating an individual
	# Number of generations/Number of itterations
	global NGen
	CXPB, MUTPB, NGen = 0.5, 0.2, 25

	print("Start of evolution")
	
	# Evaluate the entire population
	fitnesses = list(map(toolbox.evaluate, pop))
	for ind, fit in zip(pop, fitnesses):
		ind.fitness.values = fit
	
	print("  Evaluated %i individuals" % len(pop))

	# Extracting all the fitnesses of 
	fits = [ind.fitness.values[0] for ind in pop]

	# Begin the evolution
	for g in range(NGen):

		gen = g+1
		print("-- Generation %i --" % gen)
		
		# Select the next generation individuals
		offspring = toolbox.select(pop, len(pop))
		# Clone the selected individuals
		offspring = list(map(toolbox.clone, offspring))
	
		# Apply crossover and mutation on the offspring
		for child1, child2 in zip(offspring[::2], offspring[1::2]):

			# cross two individuals with probability CXPB
			if random.random() < CXPB:
				toolbox.mate(child1, child2)

				# fitness values of the children
				# must be recalculated later
				del child1.fitness.values
				del child2.fitness.values

		for mutant in offspring:

			# mutate an individual with probability MUTPB
			if random.random() < MUTPB:
				toolbox.mutate(mutant)
				del mutant.fitness.values
	
		# Evaluate the individuals with an invalid fitness
		invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
		fitnesses = map(toolbox.evaluate, invalid_ind)
		for ind, fit in zip(invalid_ind, fitnesses):
			ind.fitness.values = fit
		
		print("  Evaluated %i individuals" % len(invalid_ind))
		
		# The population is entirely replaced by the offspring
		pop[:] = offspring
		
		# Gather all the fitnesses in one list and print the stats
		fits = [ind.fitness.values[0] for ind in pop]
		
		length = len(pop)
		mean = sum(fits) / length
		sum2 = sum(x*x for x in fits)
		std = abs(sum2 / length - mean**2)**0.5

		Max_.append(max(fits))
		Avg_.append(mean)
		Std_.append(std)
		
		print("  Min %s" % min(fits))
		print("  Max %s" % max(fits))
		print("  Avg %s" % mean)
		print("  Std %s" % std, '\n')
	
	print("-- End of successful evolution --")
	global Best
	Best = tools.selBest(pop, 1)[0]	
	print("Best individual is %s, %s" % (Best, Best.fitness.values))

	# To access global var 'profit', To display profit due to each crop in 'Best' individual
	Fitness_value(Best)

	Total_profit = 0
	t = PrettyTable(['Crop','Planting Months', 'Harvest Months', 'Cycles', 'Root Sys', \
		'Water Req', 'Culti Cost', 'Profit'])
	for i in range(len(Best)):
		val = Best[i]
		t.add_row([Crop_name[val*12-1], ', '.join(Planting_month(val)), ', '.join(Harvest_month(val)), \
		len(Harvest_month(val)), Root_depth[val*12-1], Water_req[val*12-1], \
		len(Harvest_month(val))*Culti_cost[val*12-1], profit[i]])
		Total_profit = Total_profit + profit[i]
	print(t)
	print("Total Profit : %s " % Total_profit)

if __name__ == "__main__":
	main()

#---------------------------------------------- Visualisation ------------------------------------------------

Max_ = np.array(Max_)
x_ = np.arange(1,len(Max_)+1)

plt.bar(x_-0.2, Max_, width = 0.2,align='center', label='Max')
plt.bar(x_, Avg_, width = 0.2,align='center', label='Avg')
plt.bar(x_+0.2, Std_, width = 0.2,align='center', label='Std')
plt.axis([0, NGen+1, 0, 1.4*max(Max_)])
plt.axes().xaxis.set_major_locator(ticker.MultipleLocator(1))
plt.xlabel('Generation')
plt.ylabel('Total Profit')
plt.title('Max - Avg - Std')
plt.legend()
plt.show()

#------------------------------------------------ Debugging ---------------------------------------------------

Debug = True
Fitness_value(Best)
