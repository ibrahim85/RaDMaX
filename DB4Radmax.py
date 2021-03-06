#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: A_BOULLE & M_SOUILAH
# Radmax project

# =============================================================================
# Radmax Database panel module
# =============================================================================


import wx
from wx.lib.pubsub import pub
import wx.lib.agw.genericmessagedialog as GMD
import wx.lib.scrolledpanel as scrolled

import Parameters4Radmax as p4R
from Parameters4Radmax import P4Rm
from Calcul4Radmax import Calcul4Radmax

from ObjectListView import FastObjectListView, ColumnDefn
from ObjectListView import Filter

from datetime import datetime, timedelta
from time import strftime, localtime

import os
from sys import platform as _platform
import pickle
from math import floor, log

from Icon4Radmax import prog_icon_curve, _bp_btn2
from Settings4Radmax import TextValidator

from sqlalchemy import Column, Integer, String, Float, BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

import logging

logger = logging.getLogger(__name__)

pubsub_fill_list_DB = "FillListDB"
pubsub_sup_data_DB = "DeleteDataFromDB"
pubsub_refill_list_name_DB = "RefillListNameDB"
pubsub_search_combobox_DB = "SearchComboboxDB"
pubsub_update_db_nb_line = "UpdateDBNbLine"

DIGIT_ONLY = 2

Base = declarative_base()

headercolumnname = ["Date", "Exp name", "Crystal name", "Fit Algo",
                    "Fit Success", "Residual", "Geometry", "Model"]
databasename = ["date", "exp_name", "crys_name", "fit_algo",
                "fit_success", "residual", "geometry", "model"]

if 'phoenix' in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, EVT_DATE_CHANGED
    from wx.adv import DP_DROPDOWN, DP_SHOWCENTURY, DP_ALLOWNONE
else:
    from wx import DatePickerCtrl, EVT_DATE_CHANGED
    from wx import DP_DROPDOWN, DP_SHOWCENTURY, DP_ALLOWNONE


# -----------------------------------------------------------------------------
def wxdate2pydate(date):
    import datetime
    assert isinstance(date, wx.DateTime)
    if date.IsValid():
        ymd = map(int, date.FormatISODate().split('-'))
        return datetime.date(*ymd)
    else:
        return None


def convertSize(size):
    if (size == 0):
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(floor(log(size, 1024)))
    p = pow(1024, i)
    s = round(size / p, 2)
    return s, size_name[i]


# -----------------------------------------------------------------------------
class RadMaxData(Base):
    __tablename__ = 'RadMaxData'

    id = Column(Integer, primary_key=True)

    date = Column(String)
    exp_name = Column(String)
    crys_name = Column(String)
    fit_algo = Column(String)
    fit_success = Column(String)
    residual = Column(Float)
    geometry = Column(String)
    model = Column(String)

    alldata = Column(BLOB)
    spdata = Column(BLOB)
    dwpdata = Column(BLOB)
    pathDict = Column(BLOB)

    xrd_data = Column(BLOB)


# -----------------------------------------------------------------------------
class DatabaseList(object):
    def __init__(self, date, exp_name, crys_name, fit_algo, fit_success,
                 residual, geometry, model):
        """
        Constructor
        """
        self.date = date
        self.exp_name = exp_name
        self.crys_name = crys_name
        self.fit_algo = fit_algo
        self.fit_success = fit_success
        self.residual = residual
        self.geometry = geometry
        self.model = model


# -----------------------------------------------------------------------------
class DataBasePanel(scrolled.ScrolledPanel):
    def __init__(self, parent, statusbar):
        scrolled.ScrolledPanel.__init__(self, parent)
        self.statusbar = statusbar
        self.parent = parent

        self.list = FastObjectListView(self, sortable=True,
                                       style=wx.LC_REPORT | wx.SUNKEN_BORDER,
                                       size=(950, 350))
        self.list.handleStandardKeys = False
        self.list.SetEmptyListMsg("This database has no rows")
        self.list.SetEmptyListMsgFont(wx.FFont(24, wx.DEFAULT,
                                               faceName="Tekton"))

        self.width_date = 170
        self.width = 100
        self.width_model = 130
        self.check_date = 0

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnItemSelected, self.list)

        mastersizer = wx.BoxSizer(wx.HORIZONTAL)
        mastersizer.Add(self.list, 0, wx.ALL, 5)

        pub.subscribe(self.fill_list, pubsub_fill_list_DB)
        pub.subscribe(self.re_fill_list, pubsub_update_db_nb_line)

        self.SetSizer(mastersizer)
        self.Layout()
        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.initialize_list()
        c = DataBaseUse()
        c.initialize_database()

    def initialize_list(self):
        temp = []
        ic_ = prog_icon_curve.GetBitmap()
        ImageIndex = self.list.AddImages(ic_)
        self.list.AddNamedImages("date", ic_)
        for i in range(len(headercolumnname) - 1):
            if i == 0:
                temp.append(ColumnDefn(headercolumnname[i], "center",
                                       self.width_date,
                                       valueGetter=databasename[0],
                                       imageGetter=ImageIndex,
                                       maximumWidth=self.width_date))
            else:
                temp.append(ColumnDefn(headercolumnname[i], "center",
                                       self.width,
                                       valueGetter=databasename[i],
                                       maximumWidth=self.width))
        i += 1
        temp.append(ColumnDefn(headercolumnname[i], "center", self.width_model,
                               valueGetter=databasename[i],
                               maximumWidth=self.width_model))
        self.list.SetColumns(temp)

    def fill_list(self, case, l):
        a = P4Rm()
        self.Freeze()
        if case == 0:
            self.list.SetObjects(l)
        elif case == 1:
            self.list.AddObject(l)
            pub.sendMessage(pubsub_refill_list_name_DB)
            pub.sendMessage(pubsub_search_combobox_DB)
        objects = self.list.GetObjects()
        self.list.SortBy(0, ascending=False)
        if a.db_nb_line is not -1:
            self.list.SetFilter(Filter.Head(a.db_nb_line))
            self.list.RepopulateList()
        else:
            self.list.SetFilter(None)
        self.list.RefreshObjects(objects)
        self.Thaw()

    def re_fill_list(self):
        a = P4Rm()
        self.Freeze()
        if a.db_nb_line is not -1:
            self.list.SortBy(0, ascending=False)
            self.list.SetFilter(Filter.Head(a.db_nb_line))
        else:
            self.list.SetFilter(None)
        self.list.RepopulateList()
        self.Thaw()

    def OnItemSelected(self, event):
        if 'phoenix' in wx.PlatformInfo:
            currentline = event.Index
        else:
            currentline = event.m_itemIndex
        if currentline is not -1:
            obj = self.list.GetSelectedObject()
            try:
                c = DataBaseUse()
                c.on_item_selected(obj.date)
            except (AttributeError):
                pass


# -----------------------------------------------------------------------------
class DataBaseManagement(scrolled.ScrolledPanel):
    def __init__(self, parent, statusbar):
        scrolled.ScrolledPanel.__init__(self, parent)
        self.statusbar = statusbar
        self.parent = parent

        if _platform == "linux" or _platform == "linux2":
            size_StaticBox = (950, 140)
            size_combobox = (130, -1)
            font = wx.Font(10, wx.DEFAULT, wx.ITALIC, wx.BOLD)
            font_combobox = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL,
                                    False, u'Arial')
            font_TextCtrl = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL,
                                    False, u'Arial')
            vStatictextsize = 16
            size_text = (85, 22)
        elif _platform == "win32":
            size_StaticBox = (960, 140)
            size_combobox = (130, -1)
            font = wx.Font(9, wx.DEFAULT, wx.ITALIC, wx.BOLD)
            font_combobox = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL,
                                    False, u'Arial')
            font_TextCtrl = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL,
                                    False, u'Arial')
            vStatictextsize = 16
            size_text = (85, 22)
        elif _platform == 'darwin':
            size_StaticBox = (980, 140)
            size_combobox = (130, -1)
            font = wx.Font(12, wx.DEFAULT, wx.ITALIC, wx.BOLD)
            font_combobox = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL,
                                    False, u'Arial')
            font_TextCtrl = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL,
                                    False, u'Arial')
            vStatictextsize = 18
            size_text = (85, 22)

        flagSizer = wx.ALL | wx.ALIGN_CENTER_VERTICAL
        """Action box"""
        action_box = wx.StaticBox(self, -1, " Select your action ",
                                  size=size_StaticBox)
        action_box.SetFont(font)
        action_box_sizer = wx.StaticBoxSizer(action_box, wx.VERTICAL)
        in_action_box_sizer = wx.GridBagSizer(hgap=2, vgap=0)

        label_1 = b"Show selected data"
        label_2 = b"Delete some data"

        self.rb1 = wx.RadioButton(self, label=label_1, style=wx.RB_GROUP)
        self.rb2 = wx.RadioButton(self, label=label_2)

        self.rb1.Bind(wx.EVT_RADIOBUTTON, self.on_set_val)
        self.rb2.Bind(wx.EVT_RADIOBUTTON, self.on_set_val)
        self.state = [True, False]
        self.rb1.SetValue(True)

        in_action_box_sizer.Add(self.rb1, pos=(0, 0), flag=flagSizer)
        in_action_box_sizer.Add(self.rb2, pos=(2, 0), flag=flagSizer)
        action_box_sizer.Add(in_action_box_sizer, 0, wx.ALL, 5)

        """ Id part """
        self.search_Id = wx.NewId()
        self.cb_name_Id = wx.NewId()
        self.name_Id = wx.NewId()
        self.cb_crystal_Id = wx.NewId()
        self.crystal_Id = wx.NewId()
        self.cb_geom_Id = wx.NewId()
        self.geom_Id = wx.NewId()
        self.cb_model_Id = wx.NewId()
        self.model_Id = wx.NewId()
        self.cb_date_Id = wx.NewId()
        self.date_Id = wx.NewId()

        self.Id_cb_list = [self.cb_name_Id, self.cb_crystal_Id,
                           self.cb_geom_Id, self.cb_model_Id, self.cb_date_Id]
        self.Id_combo_list = [self.name_Id, self.crystal_Id,
                              self.geom_Id, self.model_Id]

        cb_name = wx.CheckBox(self, id=self.cb_name_Id, label='Name',
                              pos=(20, 20))
        cb_name.SetValue(False)
        cb_name.Bind(wx.EVT_CHECKBOX, self.un_check_choice)
        name_choice = ["None"]
        self.name = wx.ComboBox(self, id=self.name_Id,
                                pos=(50, 30),
                                choices=name_choice,
                                style=wx.CB_READONLY,
                                size=size_combobox)
        self.name.SetFont(font_combobox)
        self.Bind(wx.EVT_COMBOBOX, self.on_select_combobox, self.name)

        cb_crystal = wx.CheckBox(self, id=self.cb_crystal_Id, label='Crystal',
                                 pos=(20, 20))
        cb_crystal.SetValue(False)
        cb_crystal.Bind(wx.EVT_CHECKBOX, self.un_check_choice)
        crystal_choice = ["None"]
        self.crystal = wx.ComboBox(self, id=self.crystal_Id,
                                   pos=(50, 30),
                                   choices=crystal_choice,
                                   style=wx.CB_READONLY,
                                   size=size_combobox)
        self.crystal.SetFont(font_combobox)
        self.Bind(wx.EVT_COMBOBOX, self.on_select_combobox, self.crystal)

        cb_geom = wx.CheckBox(self, id=self.cb_geom_Id, label='Geometry',
                              pos=(20, 20))
        cb_geom.SetValue(False)
        cb_geom.Bind(wx.EVT_CHECKBOX, self.un_check_choice)
        geom_choice = ["None"]
        self.geom = wx.ComboBox(self, id=self.geom_Id,
                                pos=(50, 30),
                                choices=geom_choice,
                                style=wx.CB_READONLY,
                                size=size_combobox)
        self.geom.SetFont(font_combobox)
        self.Bind(wx.EVT_COMBOBOX, self.on_select_combobox, self.geom)

        cb_model = wx.CheckBox(self, id=self.cb_model_Id, label='Model',
                               pos=(20, 20))
        cb_model.SetValue(False)
        cb_model.Bind(wx.EVT_CHECKBOX, self.un_check_choice)
        model_choice = ["None"]
        self.model = wx.ComboBox(self, id=self.model_Id,
                                 pos=(50, 30),
                                 choices=model_choice,
                                 style=wx.CB_READONLY,
                                 size=size_combobox)
        self.model.SetFont(font_combobox)
        self.Bind(wx.EVT_COMBOBOX, self.on_select_combobox, self.model)

        cb_date = wx.CheckBox(self, id=self.cb_date_Id, label='Date',
                              pos=(20, 20))
        cb_date.SetValue(False)
        cb_date.Bind(wx.EVT_CHECKBOX, self.un_check_choice)
        now = wx.DateTime().Today()
        self.dpc_1 = DatePickerCtrl(self, size=(120, -1),
                                    style=DP_DROPDOWN |
                                          DP_SHOWCENTURY |
                                          DP_ALLOWNONE)
        self.dpc_2 = DatePickerCtrl(self, size=(120, -1),
                                    style=DP_DROPDOWN |
                                          DP_SHOWCENTURY |
                                          DP_ALLOWNONE)
        self.Bind(EVT_DATE_CHANGED, self.on_select_combobox, self.dpc_1)
        self.Bind(EVT_DATE_CHANGED, self.on_select_combobox, self.dpc_2)
        self.dpc_1.SetValue(now)
        self.dpc_2.SetValue(now)

        date_choice = ["None"]
        self.date = wx.ComboBox(self, id=self.date_Id,
                                pos=(50, 30),
                                choices=date_choice,
                                style=wx.CB_READONLY,
                                size=size_combobox)
        self.date.SetFont(font_combobox)
        self.Bind(wx.EVT_COMBOBOX, self.on_select_combobox, self.date)

        self.search_btn = wx.Button(self, id=self.search_Id, label=" Search")
        self.search_btn.Bind(wx.EVT_BUTTON, self.on_search_in_DB)

        txt_db = u'DataBase number of lines:'
        db_nb_lines_txt = wx.StaticText(self, -1, label=txt_db,
                                        size=(180, vStatictextsize))
        self.db_nb_lines = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER,
                                       size=size_text,
                                       validator=TextValidator(DIGIT_ONLY))
        self.db_nb_lines.SetFont(font_TextCtrl)
        self.db_nb_lines.SetValue(str(100))
        P4Rm.db_nb_line = 100

        bmp = _bp_btn2.GetBitmap()
        self.nb_lines_btn = wx.BitmapButton(self, -1, bmp)
        self.nb_lines_btn.SetToolTip("Update database list")
        # self.nb_lines_btn.SetToolTipString("Update database list")
        self.Bind(wx.EVT_BUTTON, self.nb_lines_DB, id=self.nb_lines_btn.GetId())
        self.Bind(wx.EVT_TEXT_ENTER, self.nb_lines_DB, self.db_nb_lines)

        self.cb_list = [cb_name, cb_crystal, cb_geom, cb_model, cb_date]

        self.combo_list = [self.name, self.crystal,
                           self.geom, self.model, self.date]
        for i in range(len(self.combo_list)):
            self.combo_list[i].Disable()

        mastersizer = wx.BoxSizer(wx.VERTICAL)
        DBLine = wx.BoxSizer(wx.HORIZONTAL)
        choice_sizer = wx.GridBagSizer(hgap=8, vgap=4)

        DBLine.Add(db_nb_lines_txt, 0, flag=flagSizer)
        DBLine.Add(self.db_nb_lines, 0, flag=flagSizer)
        DBLine.Add(self.nb_lines_btn, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)

        choice_sizer.Add(cb_name, pos=(0, 0), flag=flagSizer)
        choice_sizer.Add(self.name, pos=(0, 1), flag=flagSizer)

        choice_sizer.Add(cb_crystal, pos=(1, 0), flag=flagSizer)
        choice_sizer.Add(self.crystal, pos=(1, 1), flag=flagSizer)

        choice_sizer.Add(cb_geom, pos=(2, 0), flag=flagSizer)
        choice_sizer.Add(self.geom, pos=(2, 1), flag=flagSizer)

        choice_sizer.Add(cb_model, pos=(3, 0), flag=flagSizer)
        choice_sizer.Add(self.model, pos=(3, 1), flag=flagSizer)

        choice_sizer.Add(cb_date, pos=(4, 0), flag=flagSizer)
        choice_sizer.Add(self.date, pos=(4, 1), flag=flagSizer)
        choice_sizer.Add(self.dpc_1, pos=(4, 2), flag=flagSizer)
        choice_sizer.Add(self.dpc_2, pos=(4, 3), flag=flagSizer)

        choice_sizer.Add(self.search_btn, pos=(6, 0), flag=flagSizer)

        mastersizer.Add(action_box_sizer, 0, wx.ALL, 5)
        mastersizer.Add(DBLine, 0, wx.ALL, 10)
        mastersizer.Add(choice_sizer, 0, wx.ALL, 10)

        pub.subscribe(self.on_delete_data,
                      pubsub_sup_data_DB)
        pub.subscribe(self.on_add_new_name_to_combobox,
                      pubsub_refill_list_name_DB)
        pub.subscribe(self.on_search_in_DB,
                      pubsub_search_combobox_DB)

        self.SetSizer(mastersizer)
        self.Layout()
        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.on_fill_combobox()

    def on_set_val(self, event):
        self.state = []
        state1 = self.rb1.GetValue()
        state2 = self.rb2.GetValue()
        self.state = [state1, state2]

    def on_fill_combobox(self):
        a = P4Rm()
        choice_list = []
        c = DataBaseUse()
        c.on_read_part_DB()

        if P4Rm.DBDict['name']:
            choice_list.append(a.DBDict['name'])
        else:
            choice_list.append(["List empty"])
        choice_list.append(a.crystal_list)
        choice_list.append(p4R.sample_geometry)
        choice_list.append(p4R.Strain_DW_choice)
        choice_list.append(["equal", "=<", ">=", "between"])

        for i in range(len(self.combo_list)):
            self.combo_list[i].SetItems(choice_list[i])
            self.combo_list[i].SetStringSelection(choice_list[i][0])

        self.dpc_1.Hide()
        self.dpc_2.Hide()

    def on_add_new_name_to_combobox(self):
        a = P4Rm()
        if not a.PathDict['project_name'] in a.DBDict['name']:
            c = DataBaseUse()
            c.on_read_part_DB()
            self.name.SetItems(a.DBDict['name'])
            self.name.SetStringSelection(a.DBDict['name'][0])
            self.Layout()
            self.SetAutoLayout(1)

    def un_check_choice(self, event):
        widget = event.GetId()
        isChecked = event.GetEventObject().GetValue()
        indexx = self.Id_cb_list.index(widget)
        if isChecked:
            self.combo_list[indexx].Enable()
        else:
            self.combo_list[indexx].Disable()
        if widget == self.cb_date_Id:
            if isChecked:
                self.dpc_1.Show()
                if self.date.GetStringSelection() == 'between':
                    self.dpc_2.Show()
            else:
                self.dpc_1.Hide()
                self.dpc_2.Hide()

    def on_select_combobox(self, event):
        widget = event.GetId()
        val = event.GetString()
        if widget == self.date_Id:
            if val == 'between':
                self.dpc_2.Show()
            else:
                self.dpc_2.Hide()

    def nb_lines_DB(self, event):
        obj = self.db_nb_lines.GetValue()
        P4Rm.db_nb_line = int(obj)
        pub.sendMessage(pubsub_update_db_nb_line)

    def on_search_in_DB(self, event=None):
        list_temp = []
        P4Rm.DBDict['choice_state'] = self.rb1.GetValue()
        for i in range(len(self.cb_list)):
            if self.cb_list[i].IsChecked():
                list_temp.append(self.combo_list[i].GetStringSelection())
            else:
                list_temp.append(None)
        P4Rm.DBDict['choice_combo'] = list_temp
        if self.cb_list[-1].IsChecked():
            P4Rm.DBDict['date_1'] = '{:%Y-%m-%d %H:%M:%S}'.format(wxdate2pydate(self.dpc_1.GetValue()))
            P4Rm.DBDict['date_2'] = '{:%Y-%m-%d %H:%M:%S}'.format(wxdate2pydate(self.dpc_2.GetValue()))
        c = DataBaseUse()
        c.on_search_in_DB()

    def on_delete_data(self):
        a = P4Rm()
        _msg = "Do you really want to delete these datas?"
        dlg = GMD.GenericMessageDialog(None, _msg, "Confirm Suppression",
                                       agwStyle=wx.OK | wx.CANCEL |
                                                wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            c = DataBaseUse()
            c.on_delete_data()
            self.on_fill_combobox()
            state1 = self.rb1.SetValue(True)
            state2 = self.rb2.SetValue(False)
            self.state = [state1, state2]
            for i in range(len(self.cb_list)):
                self.cb_list[i].SetValue(False)
                self.combo_list[i].Disable()
            empty = a.DBDict['session'].query(RadMaxData).first()
            if empty is None:
                s = a.DBDict['session'].query(RadMaxData).order_by(RadMaxData.id)
                c.on_read_database_and_fill_list(s)
            else:
                self.on_search_in_DB()


# -----------------------------------------------------------------------------
# noinspection PyRedundantParentheses
class DataBaseUse():
    @staticmethod
    def create_engine(path):
        if _platform == "linux" or _platform == "linux2" or _platform == 'darwin':
            # Unix/Mac - 4 initial slashes in total
            P4Rm.DBDict['engine'] = create_engine('sqlite:////' + path)
        elif _platform == "win32":
            P4Rm.DBDict['engine'] = create_engine(r'sqlite:///' + path)

    def initialize_database(self):
        """
        Create an engine that stores data in the local directory's
        sqlalchemy_example.db file.
        """
        a = P4Rm()
        logger.log(logging.WARNING, 'Loading or creates database')

        if not os.path.isdir(p4R.database_path):
            msg = p4R.database_path + " is not present, creates one !"
            logger.log(logging.WARNING, msg)
            os.makedirs(p4R.database_path)
        path = os.path.join(p4R.database_path, p4R.Database_name + '.db')
        if not os.path.isfile(path):
            msg = p4R.Database_name + " is not present, creates one !"
            logger.log(logging.WARNING, msg)

        self.create_engine(path)
        Base.metadata.create_all(a.DBDict['engine'])

        """ test size of the DB """
        statinfo = os.stat(path)
        size, size_name = convertSize(statinfo.st_size)
        if size_name in ["MB"]:
            if size > 500:
                print ("Size of the Database file is too high: ",
                       '%s %s' % (size, size_name))
                print ("Making of backup file")
                old_name = os.path.join(p4R.database_path,
                                        p4R.Database_name + '.db')
                new_name = os.path.join(p4R.database_path,
                                        p4R.Database_name + '_backup.db')
                msg = ("Size of the Database file is too high, " +
                       "create a backup file")
                logger.log(logging.WARNING, msg)
                os.rename(old_name, new_name)
                self.create_engine(path)
                Base.metadata.create_all(a.DBDict['engine'])

        Base.metadata.bind = a.DBDict['engine']
        DBSession = sessionmaker(bind=a.DBDict['engine'])
        P4Rm.DBDict['session'] = DBSession()

        empty = a.DBDict['session'].query(RadMaxData).first()
        if empty:
            s = a.DBDict['session'].query(RadMaxData).order_by(RadMaxData.id)
            self.on_read_database_and_fill_list(s)

    @staticmethod
    def on_read_database_and_fill_list(search):
        list_temp = []
        for instance in search:
            date = instance.date
            exp_name = instance.exp_name
            crys_name = instance.crys_name
            fit_algo = instance.fit_algo
            fit_success = instance.fit_success
            residual = instance.residual
            geometry = instance.geometry
            model = instance.model
            list_temp.append(DatabaseList(str(date), str(exp_name),
                                          str(crys_name), str(fit_algo),
                                          str(fit_success), str(residual),
                                          str(geometry), str(model)))
        pub.sendMessage(pubsub_fill_list_DB, case=0, l=list_temp)

    @staticmethod
    def on_fill_database_and_list(success):
        a = P4Rm()
        current_time = localtime()
        date = strftime('%Y-%m-%d %H:%M:%S', current_time)
        exp_name = a.PathDict['project_name']
        crys_name = a.AllDataDict['crystal_name']
        fit_algo = p4R.FitAlgo_choice[a.fit_type]
        fit_success = p4R.FitSuccess[success]
        residual = round(a.residual_error, 4)
        geometry = p4R.sample_geometry[int(a.AllDataDict['geometry'])]
        model = p4R.Strain_DW_choice[int(a.AllDataDict['model'])]

        alldata = pickle.dumps(a.AllDataDict, protocol=2)
        spdata = pickle.dumps(a.ParamDict['sp'], protocol=2)
        dwpdata = pickle.dumps(a.ParamDict['dwp'], protocol=2)
        pathDict = pickle.dumps(a.PathDict, protocol=2)
        xrd_data = pickle.dumps(a.ParamDict['data_xrd'], protocol=2)

        data = RadMaxData(date=date, exp_name=exp_name, crys_name=crys_name,
                          fit_algo=fit_algo, fit_success=fit_success,
                          residual=residual, geometry=geometry, model=model,
                          alldata=alldata, spdata=spdata, dwpdata=dwpdata,
                          pathDict=pathDict, xrd_data=xrd_data)
        P4Rm.DBDict['session'].add(data)
        a.DBDict['session'].commit()

        t = DatabaseList(str(date), str(exp_name), str(crys_name),
                         str(fit_algo), str(fit_success), str(residual),
                         str(geometry), str(model))
        pub.sendMessage(pubsub_fill_list_DB, case=1, l=t)

    @staticmethod
    def on_item_selected(date):
        a = P4Rm()
        b = Calcul4Radmax()

        read_exp = a.DBDict['session'].query(RadMaxData).filter(RadMaxData.date == date).one()
        P4Rm.AllDataDict = pickle.loads(read_exp.alldata)
        P4Rm.ParamDict['sp'] = pickle.loads(read_exp.spdata)
        P4Rm.ParamDict['dwp'] = pickle.loads(read_exp.dwpdata)
        P4Rm.PathDict = pickle.loads(read_exp.pathDict)
        try:
            P4Rm.ParamDict['data_xrd'] = pickle.loads(read_exp.xrd_data, encoding='latin1')
        #            encoding pour python 3 afin de lire les données enregistrees en python 2
        except (TypeError):
            P4Rm.ParamDict['data_xrd'] = pickle.loads(read_exp.xrd_data)

        b.on_load_from_Database()
        path_ini = a.PathDict['path2inicomplete']
        if not os.path.isfile(path_ini):
            P4Rm.pathfromDB = 1
        else:
            P4Rm.pathfromDB = 0

    @staticmethod
    def on_read_part_DB():
        a = P4Rm()
        read_name = a.DBDict['session'].query(func.count(RadMaxData.exp_name),
                                              RadMaxData.exp_name).group_by(RadMaxData.exp_name).all()
        P4Rm.DBDict['name'] = [name for (num, name) in read_name]

    def on_search_in_DB(self):
        a = P4Rm()
        temp = []
        test = []
        test = [RadMaxData.exp_name, RadMaxData.crys_name, RadMaxData.geometry,
                RadMaxData.model, RadMaxData.date]

        for i in range(len(a.DBDict['choice_combo'])):
            if not a.DBDict['choice_combo'][i] is None:
                if a.DBDict['choice_combo'][i] == 'equal':
                    the_day = datetime.strptime(a.DBDict['date_1'],
                                                "%Y-%m-%d %H:%M:%S")
                    next_day = the_day + timedelta(days=1)
                    next_day = '{:%Y-%m-%d %H:%M:%S}'.format(next_day)
                    temp.append(test[i] >= a.DBDict['date_1'])
                    temp.append(test[i] <= next_day)
                elif a.DBDict['choice_combo'][i] == '=<':
                    temp.append(test[i] <= a.DBDict['date_1'])
                elif a.DBDict['choice_combo'][i] == '>=':
                    temp.append(test[i] >= a.DBDict['date_1'])
                elif a.DBDict['choice_combo'][i] == 'between':
                    temp.append(test[i] >= a.DBDict['date_1'])
                    temp.append(test[i] <= a.DBDict['date_2'])
                else:
                    temp.append(test[i] == a.DBDict['choice_combo'][i])

        s = a.DBDict['session'].query(RadMaxData).filter(*temp).all()
        if a.DBDict['choice_state']:
            self.on_read_database_and_fill_list(s)
        else:
            [a.DBDict['session'].delete(x) for x in s]
            pub.sendMessage(pubsub_sup_data_DB)

    @staticmethod
    def on_delete_data():
        a = P4Rm()
        a.DBDict['session'].commit()
        a.DBDict['engine'].execute("VACUUM")
