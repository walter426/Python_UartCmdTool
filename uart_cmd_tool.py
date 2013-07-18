#!/usr/bin/env python

#Uart Command Tool
#Walter Tsui
#2011/11/11

import sys
import os
try:
	import pygtk
	"""pygtk.require("2.0")"""
except:
		pass
try:
	import gobject
	import gtk
	import gtk.glade
	
	import time
	import serial
	import Queue
	
	import threading
	import multiprocessing
except:
	sys.exit(1);

gobject.threads_init()

TxData = ''
RxData = ''

TxCmdTable = []
TotalTxCmd = 16

for i in range(0, TotalTxCmd):
	#SendButtonWidget, Sequence, CmdEntryWidget, pBuffer
	TxCmdTable.append([None, '0', None, None])
	
RxCmdTable = []
TotalRxCmd = 16

for i in range(0, TotalRxCmd):
	#SendButtonWidget, Sequence, CmdEntryWidget, pBuffer
	RxCmdTable.append([None, '0', None, None])

class SerialComm(gobject.GObject):
	__gsignals__ = {
		'SerialPortUpdated': (gobject.SIGNAL_RUN_LAST,
					gobject.TYPE_NONE,
					()),
					}
					
	def __init__(self, queue, lock):
		gobject.GObject.__init__(self)
		
		self.queue = queue
		self.lock = lock
		
		self.event_stop = None
		self.read_thread = None
	
		try:
			self.ser = serial.Serial(
						port = 'COM1',
						baudrate = 57600,
						rtscts = False,
						timeout = 5
						)			
			self.ser.close()
			
		except serial.SerialException:
			print 'The port is Occupied!'
			
		except :
			pass
					
	def start(self, UpdateHandler, Port, Baudrate, HWFlowCtrl):
		try:
			self.ser = serial.Serial(
					port = Port,
					baudrate = Baudrate,
					rtscts = HWFlowCtrl,
					timeout = 5
					)		
			
		except serial.SerialException:
			print 'The port is Occupied!'
			return None
			
		except :
			return None
		
		self.connect("SerialPortUpdated", UpdateHandler)
		
		self.event_stop = threading.Event()
		self.event_stop.clear()
		self.read_thread = threading.Thread(target = self.read, args = ())
		self.read_thread.start()
		
	def stop(self):
		if (self.event_stop != None) :
			self.event_stop.set()
	
		if (self.read_thread != None) :
			self.read_thread.join()
			self.read_thread = None

		try:
			self.ser.close()
			
		except serial.SerialException:
			print 'The port is Occupied!'
			
		except:
			print 'The port is not created'
		
	def send(self, data):
		try:
			data = data.replace(' ' ,'').decode('hex')
			self.ser.write(data)
			
		except serial.SerialException:
			print 'The port is Occupied!'
			
		except:
			print 'The port is not created'
	
	def read(self):
		while self.event_stop.is_set() == False:
			try:
				if self.ser.inWaiting():
					data = self.ser.read(self.ser.inWaiting())
					data = data.encode('hex')
					self.queue.put(data)
					self.emit("SerialPortUpdated")
					#gobject.idle_add(self.emit, "SerialPortUpdated")
				time.sleep(0.1)
			except serial.SerialException:
				print 'The port is Occupied!'
				break;
			except :
				print 'error'
				break;
				
		self.event_stop.set()

gobject.type_register(SerialComm)


class UartCMDTool_GUI:

	def __init__(self):
		self.serial_comm = None
		self.queue = None
		self.lock = None
		
		self.Port = 'COM1'
		self.Baudrate = 57600
		self.HWFlowCtrl = False
		
		#Set the Glade file
		self.gladefile = "uart_cmd_tool.glade";
		self.wTree = gtk.glade.XML(self.gladefile);
		
		#Get the Main Window
		self.window = self.wTree.get_widget("MainWindow")
				
		for i in range(0, TotalTxCmd):
			TxCmdTable[i][0] = 'TxCmdButton_Send_' + str(i + 1)
			TxCmdTable[i][2] = "TxCmdTextEntry_" + str(i + 1)
			TxCmdTable[i][3] =  self.wTree.get_widget(TxCmdTable[i][2]).get_buffer()
		
		for i in range(0, TotalRxCmd):
			RxCmdTable[i][0] = 'RxCmdButton_Send_' + str(i + 1)
			RxCmdTable[i][2] = "RxCmdTextEntry_" + str(i + 1)
			RxCmdTable[i][3] =  self.wTree.get_widget(RxCmdTable[i][2]).get_buffer()
		
		self.TxEnterCmdEntry = self.wTree.get_widget("TxEnterCmdEntry_1")
		self.TxEnterCmdEntryBuffer = self.TxEnterCmdEntry.get_buffer()
		
		self.RxCmdBuffer = '';
		
		self.RawCmdExchangeView = self.wTree.get_widget("RawCmdExchangeView")
		self.RawCmdExchangeBuffer = self.RawCmdExchangeView.get_buffer()

		self.TranslatedCmdExchangeView = self.wTree.get_widget("TranslatedCmdExchangeView")
		self.TranslatedCmdExchangeBuffer = self.TranslatedCmdExchangeView.get_buffer()
		
		dic = {#Main Window Event
				"on_MainWindow_destroy": self.on_MainWindow_destroy,
				"on_CommCtrlButton_Start_clicked": self.on_CommCtrlButton_Start_clicked,
				"on_CommCtrlButton_Stop_clicked": self.on_CommCtrlButton_Stop_clicked,
				"on_UartConfigCombobox_1_changed": self.on_UartConfigCombobox_1_changed,
				"on_UartConfigCombobox_2_changed": self.on_UartConfigCombobox_2_changed,
				"on_UartConfigCombobox_3_changed": self.on_UartConfigCombobox_3_changed,
				"on_CmdWindowManaButton_Clear_clicked": self.on_CmdWindowManaButton_Clear_clicked,
				"on_CmdWindowManaButton_SaveLog_clicked": self.on_CmdWindowManaButton_SaveLog_clicked,
				"on_TxcmdWindowButton_ClearAll_clicked": self.on_TxcmdWindowButton_ClearAll_clicked,
				"on_TxEnterCmdButton_Send_clicked": self.on_TxEnterCmdButton_Send_clicked,
				"on_TxCmdButton_Send_clicked": self.on_TxCmdButton_Send_clicked,
				"on_TxCmdTextEntry_button_press_event": self.on_TxCmdTextEntry_button_press_event,
				"on_RxcmdWindowButton_ClearAll_clicked": self.on_RxcmdWindowButton_ClearAll_clicked,
				"on_CmdConfigButton_Load_clicked": self.on_CmdConfigButton_Load_clicked,
				"on_CmdConfigButton_Save_clicked": self.on_CmdConfigButton_Save_clicked,
				}
		
		self.wTree.signal_autoconnect(dic)

	#Main Window Event	
	def on_MainWindow_destroy(self, widget)	:
		if (self.serial_comm != None) :
			self.serial_comm.stop()
		
		gtk.main_quit()
		
	def on_CmdConfigButton_Load_clicked(self, widget):
		dialog = gtk.FileChooserDialog("Open..",
                               self.window,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
	
		response = dialog.run()
		
		if response == gtk.RESPONSE_OK:
			self.LoadCommandConfigFile(dialog.get_filename())

		dialog.destroy()
	
	def on_CmdConfigButton_Save_clicked(self, widget):
		dialog = gtk.FileChooserDialog("Save as..",
                               self.window,
                               gtk.FILE_CHOOSER_ACTION_SAVE,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_SAVE_AS, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		dialog.set_do_overwrite_confirmation(True)
		dialog.connect("confirm-overwrite", self.confirm_overwrite_callback)
	
		response = dialog.run()

		if response == gtk.RESPONSE_OK:
			self.SaveCommandConfigFile(dialog.get_filename())

		dialog.destroy()
		
	def on_CommCtrlButton_Start_clicked(self,widget):
		if(self.queue != None) :
			del self.queue
			
		self.queue = Queue.Queue()
		
		if(self.queue != None) :
			del self.lock
			
		self.lock = threading.Lock()
		
		if(self.serial_comm != None) :
			del self.serial_comm
			
		self.serial_comm = SerialComm(self.queue, self.lock)
		self.serial_comm.start(self.PrintRxCmd, self.Port, self.Baudrate, self.HWFlowCtrl)
		
		if (self.serial_comm.read_thread != None) :
			widget.set_sensitive(False)
			self.wTree.get_widget("UartConfigCombobox_1").set_sensitive(False)
			self.wTree.get_widget("UartConfigCombobox_2").set_sensitive(False)
			self.wTree.get_widget("UartConfigCombobox_3").set_sensitive(False)
		
			self.RawCmdExchangeBuffer.insert_at_cursor("Start\n")
		else:
			print 'The port is Occupied!'
		
	def on_CommCtrlButton_Stop_clicked(self,widget):
		if (self.serial_comm != None) :
			self.serial_comm.stop()
		
		self.wTree.get_widget("CommCtrlButton_Start").set_sensitive(True)
		self.wTree.get_widget("UartConfigCombobox_1").set_sensitive(True)
		self.wTree.get_widget("UartConfigCombobox_2").set_sensitive(True)
		self.wTree.get_widget("UartConfigCombobox_3").set_sensitive(True)
			
		self.RawCmdExchangeBuffer.insert_at_cursor("Stop\n")
		
	def on_UartConfigCombobox_1_changed(self,widget):
		model = widget.get_model()
		index = widget.get_active()
		self.Port = model[index][0]
		
	def on_UartConfigCombobox_2_changed(self,widget):
		model = widget.get_model()
		index = widget.get_active()
		self.Baudrate = model[index][0]
		
	def on_UartConfigCombobox_3_changed(self,widget):
		index = widget.get_active()
		self.HWFlowCtrl = not bool(index)
		
	def on_CmdWindowManaButton_Clear_clicked(self,widget):
		self.RawCmdExchangeBuffer.set_text("")
		self.TranslatedCmdExchangeBuffer.set_text("")

	def on_CmdWindowManaButton_SaveLog_clicked(self,widget):
	
		buffer = self.RawCmdExchangeBuffer
		LOG = open('cmd_log.txt', 'w')
		LOG.write(buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(),True))
		LOG.close()
		
		buffer = self.TranslatedCmdExchangeBuffer
		LOG = open('cmd_log_translated.txt', 'w')
		LOG.write(buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(),True))
		LOG.close()
		
	def on_TxEnterCmdButton_Send_clicked(self,widget):
		if (self.serial_comm != None) :
			TxData = self.TxEnterCmdEntryBuffer.get_text().upper()
			if(len(TxData) > 0):
				self.serial_comm.send(TxData)
				self.RawCmdExchangeBuffer.insert_at_cursor("S: " + TxData + "\n")
				
				found = False
				
				if(TotalTxCmd > 0):
					for i in range(0, TotalTxCmd):
						if(TxCmdTable[i][1].replace(' ', '').upper() ):
							self.TranslatedCmdExchangeBuffer.insert_at_cursor("S: " + TxCmdTable[i][3].get_text() + "\n")
							found == True
							break
				
				if(found == False):
					self.TranslatedCmdExchangeBuffer.insert_at_cursor("S: " + TxData + "\n")
	
	def PrintRxCmd(self, obj):
		if (self.serial_comm.read_thread != None) :
			self.lock.acquire()
			
			RxData = self.queue.get().upper()
			
			self.RawCmdExchangeBuffer.insert_at_cursor("R: " + RxData + "\n")
			
			found = False
				
			if(TotalRxCmd > 0):
				for i in range(0, TotalRxCmd):
					RxSeq = RxCmdTable[i][1].replace(' ', '').upper()
					if(len(RxSeq) > 0 and RxSeq == RxData):
						self.TranslatedCmdExchangeBuffer.insert_at_cursor("R: " + RxCmdTable[i][3].get_text() + "\n")
						found == True
						break
				
			if(found == False):
				self.TranslatedCmdExchangeBuffer.insert_at_cursor("R: " + RxData + "\n")
			
			self.lock.release()

	def on_TxcmdWindowButton_ClearAll_clicked(self, widget):
		for i in range(0, TotalTxCmd):
			TxCmdTable[i][1] = '0'
			TxCmdTable[i][3].set_text('', -1)
	
	def on_RxcmdWindowButton_ClearAll_clicked(self, widget):
		for i in range(0, TotalRxCmd):
			RxCmdTable[i][1] = '0'
			RxCmdTable[i][3].set_text('', -1)
		
	def on_TxCmdButton_Send_clicked(self, widget):
		if (self.serial_comm != None) :
			widget_name = widget.get_name()
			for i in range(0, TotalTxCmd):
				if(widget_name == TxCmdTable[i][0]):
					TxData = TxCmdTable[i][1]
					
					if(len(TxData) > 0):
						self.serial_comm.send(TxData)
						self.RawCmdExchangeBuffer.insert_at_cursor("S: " + TxData + "\n")
						self.TranslatedCmdExchangeBuffer.insert_at_cursor("S: " + TxCmdTable[i][3].get_text() + "\n")
						
					break;
	
	def on_TxCmdTextEntry_button_press_event(self, widget, event):
		dialog = gtk.MessageDialog(
								self.window,
								gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
								gtk.MESSAGE_INFO,
								gtk.BUTTONS_OK,
								None)
								
		if(len(TxCmdTable)):
			for i in range(0, len(TxCmdTable)):
				if TxCmdTable[i][2] == widget.get_name():
					CmdSeq = TxCmdTable[i][1]
					CmdName = TxCmdTable[i][3].get_text()
					break;						
		
		#dialog.set_markup('Please enter the command <b>name</b> and <b>sequence</b>:')
		dialog.format_secondary_markup('Please enter the command <b>name</b> and <b>sequence</b>:')

		CmdNameEntry = gtk.Entry()
		CmdSeqEntry = gtk.Entry()

		CmdNameEntry.set_text(CmdName)
		CmdSeqEntry.set_text(CmdSeq)
		
		CmdNameHbox = gtk.HBox()
		CmdNameHbox.pack_start(gtk.Label("Name:"), False, 5, 5)
		CmdNameHbox.pack_end(CmdNameEntry)
	
		CmdSeqHbox = gtk.HBox()
		CmdSeqHbox.pack_start(gtk.Label("Sequence:"), False, 5, 5)
		CmdSeqHbox.pack_end(CmdSeqEntry)
		
		dialog.vbox.pack_start(CmdNameHbox , True, True, 0)
		dialog.vbox.pack_end(CmdSeqHbox)
		dialog.show_all()
		
		response = dialog.run()

		if response != gtk.RESPONSE_OK:
			return
			
		CmdName = CmdNameEntry.get_text()
		CmdSeq = CmdSeqEntry.get_text().upper()
			
		dialog.destroy()
		
		widget_name = widget.get_name()
		
		TxCmdTable[i][1] = CmdSeq
		TxCmdTable[i][3].set_text(CmdName, -1)
		
		'''
		if(len(TxCmdTable)):
			for i in range(0, len(TxCmdTable)):
				if TxCmdTable[i][2] == widget.get_name():
					TxCmdTable[i][1] = CmdSeq
					TxCmdTable[i][3].set_text(CmdName, -1)
					break;
		'''
		
	def LoadCommandConfigFile(self, FileName):
		CFG = open(FileName)
		
		TxCmdIndex = 0
		RxCmdIndex = 0
		row = 0
		mode = None
		
		while 1:
			row += 1
			line = CFG.readline()
			
			if not line:
				break;
			
			line = line.rstrip('\n').strip(' ').rstrip(' ')
			if not line:
				continue
				
			if(line == 'Tx Command Set'):
				mode = 1
				continue
				
			elif(line == 'Rx Command Set'):
				mode = 2
				continue
				
			elif(line.find(',') < 0):
				print 'unexpected content in the configuration file, ignore line ' + str(row) + ' now...'
				continue
			
			line = line.split(',')
		
			CmdName = line[0].strip(' ').rstrip(' ')
			CmdSeq = line[1].upper()
		
			if(mode == 1 and TxCmdIndex < TotalTxCmd):
				TxCmdTable[TxCmdIndex][1] = CmdSeq
				TxCmdTable[TxCmdIndex][3].set_text(CmdName, -1)
				TxCmdIndex += 1
				
			elif(mode == 2 and RxCmdIndex < TotalRxCmd):
				RxCmdTable[RxCmdIndex][1] = CmdSeq
				RxCmdTable[RxCmdIndex][3].set_text(CmdName, -1)
				RxCmdIndex += 1
		
	#Save File Chooser Event
	def confirm_overwrite_callback(self, chooser):
		return gtk.FILE_CHOOSER_CONFIRMATION_CONFIRM 
		'''
		uri = chooser.get_uri()

		if is_uri_read_only(uri):
			if user_wants_to_replace_read_only_file (uri):
				return gtk.FILE_CHOOSER_CONFIRMATION_ACCEPT_FILENAME
			else:
				return gtk.FILE_CHOOSER_CONFIRMATION_SELECT_AGAIN
		else:
		# fall back to the default dialog
			return gtk.FILE_CHOOSER_CONFIRMATION_CONFIRM 
		'''
		
	def SaveCommandConfigFile(self, FileName):
		CFG = open(FileName, 'w')

		if(len(TxCmdTable)):
			CFG.write('Tx Command Set\n')
			
			for i in range(0, len(TxCmdTable)):
				if TxCmdTable[i][3].get_text() != '':
					CFG.write(TxCmdTable[i][3].get_text() + ', ' + TxCmdTable[i][1] +'\n')
				else:
					CFG.write('unknown' + ',' + TxCmdTable[i][1] +'\n')
		
		if(len(RxCmdTable)):
			CFG.write('Rx Command Set\n')
			
			for i in range(0, len(RxCmdTable)):
				if RxCmdTable[i][3].get_text() != '' :
					CFG.write(RxCmdTable[i][3].get_text() + ', ' + RxCmdTable[i][1] +'\n')
				else:
					CFG.write('unknown' + ',' + RxCmdTable[i][1] +'\n')
	
	
if __name__ == "__main__":
	GUI = UartCMDTool_GUI();
	gtk.threads_enter()
	gtk.main();
	gtk.threads_leave()
