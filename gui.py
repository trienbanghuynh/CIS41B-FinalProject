# Authors: Marcel Gunadi, Trien Bang Huynh and Minh Duc Vo

import matplotlib
matplotlib.use('TkAgg')               
import tkinter as tk                 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  
import matplotlib.pyplot as plt	
import tkinter.messagebox as tkmb
from plotting import Plotter
from vector import Vector
import sqlite3
import numpy as np
import json
from database import makeDatabase

class MainWin(tk.Tk):
    '''
    The main class will display tution statistic of states and interact with users to view the plots and process their choices
    '''
  
    DB = 'lab.db'
    def __init__(self):
        super().__init__()
        self.title("Final project")

        makeDatabase(self.DB)

        self._plotter = Plotter()
        self._vector = Vector()
        self._scatterSelection = ()
        self._conn = sqlite3.connect(self.DB)
        self._cur = self._conn.cursor()

        with open('values.json', 'r') as f:
            value = json.load(f)

        self._values = np.array(value, dtype = np.float32)

        # Title of the app
        tk.Label(self, text="Data Analysis and Prediction", fg="blue",font=('Times', 17)).grid(row=0, column=0, columnspan=4, pady=10)

        # Create buttons

        tk.Button(self, text="Scatter plots", command=self.showScatterPlot).grid(row=1, column=0, padx=10, pady=10, ipady=2)
        tk.Button(self, text="Data comparison", command= self.compareData).grid(row=1, column=1, padx=10, pady=10, ipady=2)
        tk.Button(self, text="Trendline and prediction", command= self.showTrend).grid(row=1, column=2, padx=10, pady=10, ipady=2)
        tk.Button(self, text="Estimation", command= self.showEstimate).grid(row=1, column=3, padx=10, pady=10, ipady=2)
        
        self.protocol("WM_DELETE_WINDOW", self.close_window)

    def showScatterPlot(self):
        
        dialogWin = DialogWin(self)
        dialogWin.scatter()
        self.wait_window(dialogWin)
        
        res = dialogWin.getSelectedScatter()
      
        if len(res) == 1:
            PlotWin(self, self._plotter.by_year, res[0])
        elif len(res) == 2:
            PlotWin(self, self._plotter.year_to_year,res[0], res[1])
    
    def compareData(self):
        self._cur.execute('''SELECT Company FROM Company''')
        companyList = []
        for tup in self._cur.fetchall():
            companyList.append(tup[0])

        dialogWin  = DialogWin(self)
        dialogWin.compare(companyList)
        self.wait_window(dialogWin)
        retCompList = dialogWin.getCompList()
        rank  = dialogWin.getEntryRank()
       
        if rank == 0:
            if len(retCompList) > 1:
                if dialogWin.getRadioCompare() == "profit":
                    PlotWin(self, self._plotter.compare_companies_by_profit, retCompList)
                else:
                    PlotWin(self, self._plotter.compare_companies_by_revenue, retCompList)
        else:
            if dialogWin.getRadioCompare() == "profit":
                PlotWin(self, self._plotter.profit_compare_nth_rank_companies, rank)
            else:
                PlotWin(self, self._plotter.revenue_compare_nth_rank_companies, rank)

    def showTrend(self):
        self._cur.execute('''SELECT Company FROM Company''')
        companyList = []
        for tup in self._cur.fetchall():
            companyList.append(tup[0])
        dialogWin  = DialogWin(self)
        dialogWin.predict([f"func power of {i}" for i in range(1,11)], companyList)
        self.wait_window(dialogWin)
        retFuncSel = dialogWin.getFuncSelection()
        retCompSel = dialogWin.getCompSelection()
        if retCompSel != None:
            if dialogWin.getRadioPredict() == "profit":
                PlotWin(self, self._plotter.predict_company_profit, retCompSel,retFuncSel)
            else:
                PlotWin(self, self._plotter.predict_company_revenue, retCompSel, retFuncSel)

    def showEstimate(self):
        dialogWin  = DialogWin(self)
        dialogWin.estimate()
        self.wait_window(dialogWin)
        retInput = []
        if not dialogWin.getEstRevenue() and not dialogWin.getEstProfit():
            return

        if dialogWin.isYearSel():
            retInput.append(np.int32(dialogWin.getYearEst())) 

        retInput.append(np.float32(dialogWin.getEstRevenue())) 
        retInput.append(np.float32(dialogWin.getEstProfit()))  

        
        retInputNp = np.array(retInput)
        print(retInputNp)


        bestEstimate = None
        
        print(self._values.T[:, [0, 2, 3]])
        
        if dialogWin.isAngle(): # search by angle
            if dialogWin.isYearSel(): # with year selected
                if dialogWin.isLock():
                    bestEstimate = self._vector.angle_between_vectors(retInputNp, self._values.T[:, [0, 2, 3]], True)
                else:
                    bestEstimate = self._vector.angle_between_vectors(retInputNp, self._values.T[:, [0, 2, 3]], False)
            else:
                bestEstimate = self._vector.angle_between_vectors(retInputNp, self._values.T[:, [0, 2, 3]])

        else: # search by distance
            if dialogWin.isYearSel(): # with year selected
                if dialogWin.isLock():
                    bestEstimate = self._vector.distance_between_vectors(retInputNp, self._values.T[:, [0, 2, 3]], True)
                else:
                    bestEstimate =self._vector.distance_between_vectors(retInputNp, self._values.T[:, [0, 2, 3]], False)
            else:
                bestEstimate = self._vector.distance_between_vectors(retInputNp, self._values.T[:, [0, 2, 3]])
        
        index = np.argmin(bestEstimate)


        self._cur.execute('''SELECT * FROM Lab JOIN Company ON Lab.Company = Company.id WHERE Lab.id = ?''',(int(index) + 1,))

        record  = self._cur.fetchall()[0]


        tkmb.showinfo("Information",f'Year: {record[1]} \n Company: {record[-1]} \
                \n Revenue: ${record[4]:.2f} billion(s) \nProfit: ${record[5]:.2f} billion(s)' )

       
        # print("The best estimation ", f'Year {record[1]} \n Company {record[-1]} \
        #         \n Revenue {record[4]} \nProfit {record[5]}')

    def close_window(self):
        self.destroy()
        self.quit()


class DialogWin(tk.Toplevel):
    '''
    A class which interact and get input from user
    '''
    def __init__(self, master):
        super().__init__(master)
        self.grab_set()
        self.focus_set()
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.closeWin)
        self._companyList = [] # for compare plots
        self._scatterSelection = () # for scatter plot
        self._compPredictSel = None # for prediction plot
            
    def optionFilterScatter(self, selectedOption):
        '''
        Filter option menu by any change in a starting year
        '''
        tempOptions = list(filter(lambda option: option > self.selection2.get(), self.options3))
        self.optionMenu3['menu'].delete(0, 'end')
        self.selection3.set(tempOptions[0])
        for option in tempOptions:
            self.optionMenu3['menu'].add_command(label=option, command=tk._setit(self.selection3, option))
       
    def selectedScatter(self):
        if self.raSelection == 1:
            self._scatterSelection = (self.selection1.get(),)
        else:
            startYear, endYear = self.selection2.get(), self.selection3.get()
            if endYear - startYear > 20:
                tkmb.showwarning("Warning", "The label might not fit entire screen. Please select less than 20 years")
                return
            self._scatterSelection = (startYear, endYear)

        self.closeWin()

    def getSelectedScatter(self):
        return self._scatterSelection

    def scatter(self):
        
        scatterLabel = tk.Label(self, text="Scatter plots", fg="blue",font=('Times', 15))
        scatterLabel.grid(row=0, column=0, columnspan=5, padx=10, pady=10)

        
        self.selection1, self.selection2, self.selection3 = tk.IntVar(),tk.IntVar(), tk.IntVar() 
        self.options1 = [i for i in range(1955, 2023)]
        self.options2 = [i for i in range(1955, 2022)]
        self.options3 = [i for i in range(1956, 2023)]
        self.selection1.set(self.options1[0])
        self.selection2.set(self.options2[0])
        self.selection3.set(self.options3[0])

        def onRadioSelect():
            self.raSelection = radioYear.get()
            
            if self.raSelection == 1:
                self.optionMenu2.grid_forget()
                self.optionMenu3.grid_forget()
                self.optionMenu1.grid(row=2, column=0, padx=2, pady=10, sticky="nsew")    
            else:
                self.optionMenu1.grid_forget()
                self.optionMenu2.grid(row=2, column=2, padx=2, pady=10, sticky="nsew")
                self.optionMenu3.grid(row=2, column=4, padx=2, pady=10, sticky="nsew")
               

        # radio buttons
        radioYear = tk.IntVar()

        oneYearButton = tk.Radiobutton(self, text="One year", variable=radioYear, value=1, command=onRadioSelect)
        oneYearButton.grid(row=1, column=0, padx=20, pady=10)
        yearsButton = tk.Radiobutton(self, text="Year to year", variable=radioYear, value=2, command=onRadioSelect)
        yearsButton.grid(row=1, column=3, padx=20, pady=10)
      

        # optiton menu
            
        self.optionMenu1 = tk.OptionMenu(self, self.selection1, *self.options1)
        self.optionMenu1.grid_forget()
        self.optionMenu2 = tk.OptionMenu(self, self.selection2, *self.options2, command=self.optionFilterScatter)
        self.optionMenu2.grid_forget()
        self.optionMenu3 = tk.OptionMenu(self, self.selection3, *self.options3)
        self.optionMenu3.grid_forget()

    
        button = tk.Button(self, text="Click to select", font=('Times', 15), command = self.selectedScatter)
        button.grid(row=4, column=0,columnspan=5, padx=10, pady=10)

    def onClickedCompare(self):
        if not self.entry.get():
            if len(self.listboxCompare.curselection()) < 2 or len(self.listboxCompare.curselection()) > 5:
                tkmb.showerror("Error", "Please select between 2 and 5 companies.")
                self.listboxCompare.selection_clear(0, tk.END)
                return
            else:
                self._companyList = [self.listboxCompare.get(i) for i in self.listboxCompare.curselection()]

        else:
            try:
                self._rank.set(int(self.entry.get()))
            except ValueError:
                self.entry.delete(0, tk.END)
                tkmb.showerror("Error", "Rank is an integer!")
                return
            
        self.closeWin()

    def getRadioCompare(self):
        return self._radioCompare.get()
    
    def getCompList(self):
        return self._companyList

    def getEntryRank(self):
        return self._rank.get()

    def compare(self, iList):
        
        label = tk.Label(self, text="Select from 2 to 5 companies to compare or Enter a Rank")
        label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10, anchor=tk.NE)

        # listbox
        self.listboxCompare = tk.Listbox(self, height=10, width=20, selectmode='multiple')
        self.listboxCompare.pack(side=tk.RIGHT, padx=10, pady=10)
        for i in iList:
            self.listboxCompare.insert(tk.END, i)
        # self.listboxCompare.selection_set(0)

        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.listboxCompare.yview)
        self.listboxCompare.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        select = tk.Button(self, text="Click to select", font=('Times', 15), command=self.onClickedCompare)
        select.pack(side=tk.BOTTOM, padx=10, pady=10)
  

        # entry box for ranks
        self._rank = tk.IntVar()
        self._rank.set(0)
        label = tk.Label(self, text="Enter a rank to compare:")
        label.pack(side=tk.LEFT, pady=10)
        self.entry = tk.Entry(self, width=5)
        self.entry.pack(side=tk.LEFT, padx=2, pady=10)
    
        # radio button
        self._radioCompare = tk.StringVar()
        self._radioCompare.set("profit")
        profit = tk.Radiobutton(self, text="Profit", variable=self._radioCompare, value="profit")
        profit.pack(side=tk.LEFT, padx=10, pady=10)
        revenue = tk.Radiobutton(self, text="Revenue", variable=self._radioCompare, value="revenue")
        revenue.pack(side=tk.LEFT, padx=10, pady=10)
  
    def getRadioPredict(self):
        return self._radioPredict.get()

    def onClickedPredict(self):
        self._compPredictSel = self.listboxPredict.get(self.listboxPredict.curselection())
        self.closeWin()

    def getFuncSelection(self):
        return int(self.selection4.get().split()[-1])
  
    def getCompSelection(self):
        return self._compPredictSel

    def predict(self, funcList:str, compList:str):
        # label 
        label = tk.Label(self, text="Select a function and a company")
        label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10, anchor=tk.NE)
    
        # listbox
        self.listboxPredict = tk.Listbox(self, height=10, width=20)
        self.listboxPredict.pack(side=tk.RIGHT, padx=10, pady=10)
        for i in compList:
            self.listboxPredict.insert(tk.END, i)
        self.listboxPredict.selection_set(0)

        # scrollbar
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.listboxPredict.yview)
        self.listboxPredict.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        #  select button
        select = tk.Button(self, text="Click to select", font=('Times', 15), command=self.onClickedPredict)
        select.pack(side=tk.BOTTOM, padx=10, pady=10)

         # radio button
        self._radioPredict = tk.StringVar()
        self._radioPredict.set("profit")
        profit = tk.Radiobutton(self, text="Profit", variable=self._radioPredict, value="profit")
        profit.pack(side=tk.LEFT, padx=10, pady=10)
        revenue = tk.Radiobutton(self, text="Revenue", variable=self._radioPredict, value="revenue")
        revenue.pack(side=tk.LEFT, padx=10, pady=10)

        # option menu for func
        self.selection4 = tk.StringVar()
        self.selection4.set(funcList[0])
        self.optionMenu4 = tk.OptionMenu(self, self.selection4, *funcList)
        self.optionMenu4.pack(side=tk.LEFT, padx=10, pady=10)
        
    def onClickedEstimate(self):
        try:
            self._estRevenue.set(float(self.estEntry1.get()))
            self._estProfit.set(float(self.estEntry2.get()))
            # print(self._estRevenue.get(), self._estProfit.get())
        except ValueError:
            self.estEntry1.delete(0, tk.END)
            self.estEntry2.delete(0, tk.END)
            tkmb.showerror("Error", "Profit/Revenue is number!")
            return

        self.closeWin()

    def getEstProfit(self):
        return self._estProfit.get()

    def getEstRevenue(self):
        return self._estRevenue.get()

    def getYearEst(self):
        
        return self._yearSecEst.get()
    
    def isYearSel(self):
        return self._est2.get()

    def isLock(self):
        return self._est3.get()

    def isAngle(self):
        # print(self._est1)
        if self._est1.get() == "angle":
            return True
        else:
            return False

    def estimate(self):
        self.estEntry1 = tk.Entry(self, width=10)
        self.estEntry1.grid(row=0, column=1, padx=5, pady=5)
        self._estProfit = tk.DoubleVar()

        label1 = tk.Label(self, text="Enter a revenue")
        label1.grid(row=0, column= 0,  padx=5, pady=5)

        self.estEntry2 = tk.Entry(self, width=10)
        self.estEntry2.grid(row=1, column=1, padx=5, pady=5)
        label2= tk.Label(self, text="Enter a profit")
        label2.grid(row=1, column= 0, padx=5, pady=5)
        self._estRevenue = tk.DoubleVar()

        yearOption = [i for i in range(1955, 2023)]
        self._yearSecEst = tk.IntVar()
        self._yearSecEst.set(yearOption[0])
        self.optionMenuEst = tk.OptionMenu(self, self._yearSecEst, *yearOption)
        self.optionMenuEst.grid_forget()

        self._est1, self._est2, self._est3 = tk.StringVar(), tk.BooleanVar(), tk.BooleanVar()
        self._est1.set("angle")
    


        def onYearSelect():
            if self._est2.get():
                self.optionMenuEst.grid(row=3, column=2, padx=2, pady=5, sticky="nsew")
                cb2.grid(row=3, column=3, padx=10, pady=10)
            else:
                self.optionMenuEst.grid_forget()
                cb2.grid_forget()
       
        
        rb1 = tk.Radiobutton(self, text="Angle", variable=self._est1, value="angle")
        rb1.grid(row=2, column=0, padx=10, pady=10)
        rb2 = tk.Radiobutton(self, text="Distance", variable=self._est1, value="distance")
        rb2.grid(row=2, column=1, padx=10, pady=10)
        cb1 = tk.Checkbutton(self, text="Year", variable=self._est2, command=onYearSelect)
        cb1.grid(row=2, column=2, padx=10, pady=10)
        cb2 = tk.Checkbutton(self, text="Lock", variable=self._est3, command=onYearSelect)
        cb2.grid_forget()

        
        button = tk.Button(self, text="Click to select", font=('Times', 15), command=self.onClickedEstimate)
        button.grid(row = 4, columnspan=5, pady = 5)

    def closeWin(self):
        self.destroy()

class PlotWin(tk.Toplevel):
    '''
    A class to create appropriate plots.
    '''
    def __init__(self, master, plotType, *args):
        super().__init__(master)
        self.transient(master)
        fig = plt.figure(figsize = (10, 6))
        plotType(*args)
        canvas = FigureCanvasTkAgg(fig, master = self)
        canvas.get_tk_widget().grid()
        canvas.draw()

