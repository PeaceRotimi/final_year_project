import csv
import os

class BrokerLogger:
    def __init__(self,filename="broker_log.csv"):
        self.filename = filename

        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Timeslot",
                    "Bank_Balance",
                    "Active_Tariffs",
                    "Competitor_Price",
                    "Est_Imbalance",
                    "Wholesale_Cleared_Mwh"
                ])

    def log(self,timeslot,cash,no_tariffs,comp_price,esti_imbalance,cleared_energy):

        with open (self.filename,mode ='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    timeslot,round(cash,2),no_tariffs,round(comp_price,4),round(esti_imbalance,2),round(cleared_energy,2)
                ])
