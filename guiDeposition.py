
import sys
#if you are using windows you probably need tkinter instead of Tkinter
from Tkinter import *
import ttk
import tkMessageBox

#Multithreading packages
import Queue
import threading


#import deposition.py und den rest des codes in def_main(nu, T)=
import deposition 


class Checkbar(Frame):
   def __init__(self, parent=None, picks=[], side=RIGHT, anchor=W):
	  Frame.__init__(self, parent)
	  self.vars = []
	  for pick in picks:
		 var = IntVar()
		 chk = Checkbutton(self, text=pick, variable=var)
		 chk.pack(side=side, anchor=anchor, expand=YES)
		 self.vars.append(var)
   def state(self):
	  return map((lambda var: var.get()), self.vars)


class DoseCalculator(ttk.Frame):
    def __init__(self,parent=None,padding=None):
        ttk.Frame.__init__(self,padding=padding)
        self.parent = parent
        self.doSetup()
        return

    def doSetup(self):
        #Inside the window make a frame where the buttons, labels and Text fields live (not necessary)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        #define variables that should be handled by labels/text fields
        self.time = StringVar()
        self.time.set("100")
        self.timestep = StringVar()
        self.timestep.set("1")

        ttk.Entry(self, width=7, textvariable=self.time).grid(column=2, row=9, sticky=(W, E))
        ttk.Entry(self, width=7, textvariable=self.timestep).grid(column=2, row=10, sticky=(W, E))

        #Declare labels with constant text
        ttk.Label(self,text="Calculation of the dose due to deposition of nuclides.").grid(column=1, row=1, sticky=(N, E, S, W))
        ttk.Label(self,text="Comparison of the new UNSCEAR 2016 methodology with UNSCEAR 2013.").grid(column=1, row=2, sticky=(N, E, S, W))
        ttk.Label(self, text=" ").grid(column=1, row=3, sticky=W)
        ttk.Label(self, text="UNSCEAR - 2013: Time dependent location factors and occupation/age dependent occupancy factors").grid(column=1, row=4, sticky=W)
        ttk.Label(self, text="UNSCEAR - 2016: Location factor = 0.1 for indoors and indoors ocupancy = 0.8").grid(column=1, row=5, sticky=W)
        ttk.Label(self,text=" ").grid(column=1, row=6, sticky=(N, E, S, W))
        #ttk.Label(self,text="Enter nuclide: Cs137 or Cs134").grid(column=1, row=7, sticky=(E))
        ttk.Label(self,text="Select nuclide:").grid(column=1, row=7, sticky=(W))
        ttk.Label(self,text="Enter time for calculation").grid(column=1, row=9, sticky=(E))
        ttk.Label(self, text="years").grid(column=3, row=9, sticky=W)
        ttk.Label(self,text="Enter timestep for calculation").grid(column=1, row=10, sticky=(E))
        ttk.Label(self, text="day(s)").grid(column=3, row=10, sticky=W)
        #ttk.Label(self,text="  Default: 1 day").grid(column=2, row=10, sticky=(N, E, S, W))
        ttk.Label(self, text=" ").grid(column=1, row=11, sticky=W)

        ttk.Label(self,text="Choose how you want to display the graphs:").grid(column=1, row=12, sticky=(N, E, S, W))

        ttk.Label(self,text="Toggle to change the default display of the total dose graphs (linear):").grid(column=1, row=16, sticky=(N, E, S, W))

        ttk.Label(self,text="Toggle to change the default display of the dose rate graphs (logarithmic):").grid(column=1, row=17, sticky=(N, E, S, W))

        self.graphOption = Checkbar(self, ['By building type','By occupancy group'])
        self.graphOption.grid(column=1, row=14, sticky=(W))

        self.nuclideOption = Checkbar(self, ['Cs-137(+Ba-137m)','Cs-134'])
        self.nuclideOption.grid(column=1, row=8, sticky=(W))
        #self.nuclideOption = Checkbar(self, ['Cs-137(+Ba-137m)','Cs-134'])
        #self.nuclideOption.grid(column=1, row=8, sticky=(W))

        self.totdosetimeOption = Checkbar(self, ['Logarithmic'])
        self.totdosetimeOption.grid(column=1, row=16, sticky=(E))

        self.doseratetimeOption = Checkbar(self, ['Linear'])
        self.doseratetimeOption.grid(column=1, row=17, sticky=(E))

        ttk.Label(self, text=" ").grid(column=1, row=15, sticky=W)

        #Create the buttons and associate them with the functions they should trigger
        self.calcButton = ttk.Button(self, text="Calculate", command=self.calculate)
        self.calcButton.grid(column=2, row=19,sticky=(N,E,S,W))
        self.exitButton = ttk.Button(self, text="Exit", command=self.parent.destroy)
        self.exitButton.grid(column=3, row=19, sticky=W)

        #Just some padding for all the elements to make them pysically appealing
        for child in self.winfo_children(): child.grid_configure(padx=5, pady=5)

        return

    #Check if userinput is allowed.
    def checkInput(self):
        ti = float(self.time.get())
        ts = float(self.timestep.get())/365.
        if sum(self.nuclideOption.state()) == 0:
            return False
        elif sum(self.graphOption.state()) == 0:
            return False
        elif not ts > 0:
            return False
        elif ts > ti:
            return False
        return True

    #Here the calculation function for the calcButton is defined
    def calculate(self):
        try:
            if self.checkInput():
                #Read in necessary variables:
                nu = self.nuclideOption.state()
                ti = float(self.time.get())
                ts = float(self.timestep.get())/365.
                graph = self.graphOption.state()
                totdosetimeopt = self.totdosetimeOption.state()
                doseratetimeopt = self.doseratetimeOption.state()

                #Create a message that the calculation is now running
                top = Toplevel()
                top.title("Calculation running")
                Label(top, text="Please wait, I'm thinking...", padx=60, pady=25).pack()
                top.update()
                
                #Enable the calculation to run in background
                #This avoids the crashing of the interface
                #So first we need a task queue that the main thread has to work through
                q = Queue.Queue()

                #Function to put a task into the main thread queue
                def on_main_thread(func):
                    q.put(func)
                    return

                #Let the main thread check the queue if a task is there, and if so, do it
                def check_queue():
                    while True:
                        try:
                            task = q.get(block=False)
                        except Queue.Empty:
                            break
                        else:
                            self.after_idle(task)
                    self.after(100,check_queue)
                    return

                #Display message that calculations are done
                def done_mssg():
                    #tkMessageBox.showinfo("Done","Integrated Dose at T = {:} years before application of occupancy and location factors in nSv/kBqm^2: {:}".format(ti,intDose))
                    top.destroy()
                    tkMessageBox.showinfo("Done!","See output files for results and plots.")
                    enableButton()
                    return

                #enable and disable button functions
                def disableButton():
                    self.calcButton.state(['disabled'])
                    self.exitButton.state(['disabled'])
                    return
                def enableButton():
                    self.calcButton.state(['!disabled'])
                    self.exitButton.state(['!disabled'])
                    return

                #Handler for the calculation on a new thread
                def handle_calc():
                    def calculator():
                        #here the actual caclulation happens:
                        deposition.main(nu,ti,ts,graph,totdosetimeopt,doseratetimeopt)
                        #after its done give the done-mssg-task to the main thread queue
                        on_main_thread(done_mssg)
                        return
                    #Before starting the calculation, disable all buttons:
                    disableButton()
                    
                    #Use for multithreading: start a new thread and do the calculation on it:
                    #t = threading.Thread(target=calculator)
                    #t.start()

                    #Use on a single thread:
                    calculator()
                    return
                #Let the main thread start the Handler for the slave thread
                self.after(1,handle_calc)
                #Check if there is a task in the queue
                self.after(100,check_queue)

            else:
                tkMessageBox.showerror("Value Missing or not allowed!","There is a value missing in your input, or it is not allowed.")

        except ValueError:
            tkMessageBox.showerror("Value Missing or not allowed!","There is a value missing in your input, or it is not allowed.")
        return


#only execute this, if this is the main file!
if __name__=="__main__":
    #Open a new Tk instance (will be parent window)
    mGui = Tk()
    mGui.title("Nuclide Deposition Calculations")

    mainframe = DoseCalculator(mGui, padding="3 3 12 12")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

    #Start the GUI loop
    mGui.mainloop()

