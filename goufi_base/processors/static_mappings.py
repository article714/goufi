# -*- coding: utf-8 -*-
'''
Created on 3 mai 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

import re

from odoo.addons.goufi_base.utils.converters import toString

from .csv_support_mixins import CSVImporterMixin
from .processor import MultiSheetLineIterator
from .xl_base_processor import XLImporterBaseProcessor


#-------------------------------------------------------------------------------------
# CONSTANTS
AUTHORIZED_EXTS = ('xlsx', 'xls', 'csv')
DEFAULT_LOG_STRING = u" [ line %d ] -> %s"

FILE_TYPE_CSV = 0
FILE_TYPE_XL = 1

#-------------------------------------------------------------------------------------
# MAIN CLASS


class Processor(CSVImporterMixin, XLImporterBaseProcessor):

    '''
        TODO => traiter le pb des modèles avec un _ dans le nom
        TODO => traiter les CSV à une seule colonne
        TODO => traiter les fichiers XLS
    '''

    '''

    Cette classe permet de traiter des fichiers CSV, XLS ou XLSX pour importer les données qu'ils contiennent dans une instance d'Odoo

    Les fichiers sont importés depuis un répertoire (y compris les sous-répertoires) après avoir été trié par ordre alphabétique

    POUR LES FICHIERS XLS/XLSX

        * chaque feuille est importée séparément
        * le nom du modèle cible est le nom de la feuille

    POUR LES FICHIERS CSV

        * le nom du fichier est du format XX_NOM.csv
             -- XX contenant 2 chiffres pour ordonner l'import,
             -- NOM contient le nom du modèle cible en remplaçant les '.' par des '_'

             /ex, pour importer des res.partner le fichier sera nommé : 00_res_partner.csv

    TRAITEMENT DES LIGNES d'ENTETES (1ere ligne de la feuille (xls*) ou du fichier (csv)

        * la première ligne du fichier définit la façon dont la valeur des colonnes seront importées/traitées:

            -- si la cellule contient le nom d'un champs du modèle, sans modificateur, alors les données de la colonne sont affectés au champs du même nom
                    dans la base
                    /ex. si le modèle cible est res.partner, le contenu de la colonne 'name', sera affecté au champ name de l'enregistrement correspondant

            -- toutes les colonnes contenant des valeurs non retrouvées dans le modèle sont ignorées

            -- Le contenu de la colonne peut démarrer par un modificateur

                    => "ID(nom_champs)"
                            la valeur de la colonne est utilisée comme valeur unique pour retrouver les enregistrements dans la base
                            si un enregistrement existe avec une valeur du champs nom_champs égal à la valeur de la colonne alors l'enregistrement
                            est mis à jour, sinon un nouvel enregistrement est créé

                    => ">nom_champs/nom_modele_lie/nom_champs_recherche&(filtre)"
                            le champs a adresser (nom_champs) est un champs relationnel vers le modèle (nom_model_lie),
                            de type Many2One
                            pour retrouver l'enregistrement lié, on construit une chaine de recherche avec
                            [noms_champs_recherche=valeur_colonne], le filtre étant utilisé pour restreindre encore la recherche

                            si un enregistrement est trouvé dans le modèle lié, alors l'enregistrement courant est mis à jour/créé avec
                            la valeur "nom_champs" pointant vers ce dernier, sinon, une erreur est remontée et la valeur du champs est ignorée

                    => "*nom_champs/nom_modele_lie/nom_champs_recherche&(filtre)"
                            le champs a adresser (nom_champs) est un champs relationnel vers le modèle (nom_model_lie),
                            de type One2Many
                            pour retrouver les enregistrements liés, on itère sur toutes les valeurs (séparées par des ';' points virgules)
                            pour construire une chaine de recherche avec [noms_champs_recherche=valeur_colonne],
                            le filtre étant utilisé pour restreindre encore la recherche

                            pour chaque enregistrement trouvé dans le modèle lié, l'enregistrement courant est mis à jour/créé en ajoutant
                            à la collection  "nom_champs" un pointeur vers l'enregistrement cible

                    => "+nom_champs/nom_modele_lie"

                            le champs a adresser (nom_champs) est un champs relationnel vers le modèle (nom_model_lie),
                            de type Many2One

                            on crée un ou plusieurs enregistrements cibles avec les valeurs données sous forme de dictionnaire
                            (/ex.: {'name':'Mardi','dayofweek':'1',...})
                            séparés par des ';' points virgules


    '''

    def __init__(self, parent_config):

        XLImporterBaseProcessor.__init__(self, parent_config)

        # variables use during processing
        # My own fields

        self.o2mFields = {}
        self.m2oFields = {}
        self.stdFields = []
        self.idFields = []

        self.fileType = FILE_TYPE_CSV

        # parameters
        self.csv_separator = ","
        self.csv_string_separator = "\""
        for param in parent_config.processor_parameters:
            if param.name == u'csv_separator':
                self.csv_separator = param.value
            if param.name == u'csv_string_separator':
                self.csv_string_separator = param.value

    #-------------------------------------------------------------------------------------
    # recherche les noms de champs a mettre en relation

    def process_tab_header(self, tab=None,  headerrow=None):

        self.o2mFields = {}
        self.m2oFields = {}
        self.stdFields = []
        self.idFields = {}

        self.logger.info("NEW SHEET:  Import data for model " + toString(self.target_model))

        target_fields = None

        if self.target_model == None:
            self.logger.error("FAILED => NO TARGET MODEL FOUND")
            return None
        else:
            target_fields = self.target_model.fields_get_keys()

        header = None
        if self.fileType == FILE_TYPE_CSV:
            header = CSVImporterMixin.get_row_values(self, tab, row=headerrow)
        else:
            header = XLImporterBaseProcessor.get_row_values(self, tab, row=headerrow)

        for val in header:

            hname = toString(val)

            if re.match(r'ID(.*)', hname):
                v = hname.replace('ID(', '')
                v = v[:-1]
                if v in target_fields:
                    self.idFields[hname] = v
                    self.stdFields.append(v)
                else:
                    self.logger.debug(toString(v) + "  -> field not found, IGNORED")
            elif re.match(r'\*.*', hname):
                v = hname.replace('*', '')
                vals = [0] + v.split('/')
                v = vals[1]
                if v in target_fields:
                    self.o2mFields[hname] = vals
                else:
                    self.logger.debug(toString(v) + "  -> field not found, IGNORED")
            elif re.match(r'\+.*', hname):
                v = hname.replace('+', '')
                vals = [1] + v.split('/')
                v = vals[1]
                if v in target_fields:
                    self.o2mFields[hname] = vals
                else:
                    self.logger.debug(toString(v) + "  -> field not found, IGNORED")
            elif re.match(r'\>.*', hname):
                v = hname.replace('>', '')
                vals = [0] + v.split('/')
                v = vals[1]
                if v in target_fields:
                    self.m2oFields[hname] = vals
                    if re.match(r'.*\&.*', self.m2oFields[hname][3]):
                        (_fieldname, cond) = self.m2oFields[hname][3].split('&')
                        self.m2oFields[hname][3] = _fieldname
                        self.m2oFields[hname].append(eval(cond))
                else:
                    self.logger.debug(" %s -> field not found, IGNORED", toString(v))
            else:
                if hname in target_fields:
                    self.stdFields.append(hname)
                else:
                    self.logger.debug(" %s -> field not found, IGNORED", toString(hname))

        if len(self.stdFields) + len(self.idFields) + len(self.m2oFields) + len(self.o2mFields) > 0:
            return header
        else:
            return None

    #-------------------------------------------------------------------------------------
    # process a row of data

    def map_values(self, row):
        for f in row:
            if row[f] == "False" or row[f] == "True":
                row[f] = eval(row[f])
            elif row[f] == None:
                del(row[f])
        return row

    def process_values(self, line_index, data_values):

        currentObj = None
        TO_BE_ARCHIVED = False

        # Attention, il y a un champs ID => on traite les mises à jour et les suppressions ou archivages
        # suppression/archivage si une valeur contient "supprimer de la base odoo

        if len(self.idFields) > 0:

            # calcul des critères de recherche
            search_criteria = []

            for k in self.idFields:
                keyfield = self.idFields[k]
                value = None
                if k in data_values:
                    value = data_values.pop(k)
                    data_values[keyfield] = value
                if value != None and value != str(''):
                    search_criteria.append((keyfield, '=', value))

            # ajout d'une clause pour rechercher tous les enregistrements
            CAN_BE_ARCHIVED = ('active' in self.target_model.fields_get_keys())
            if CAN_BE_ARCHIVED:
                search_criteria.append('|')
                search_criteria.append(('active', '=', True))
                search_criteria.append(('active', '=', False))

            # recherche d'un enregistrement existant
            found = self.target_model.search(search_criteria)

            if len(found) == 1:
                currentObj = found[0]
            elif len(found) > 1:
                self.logger.warning(DEFAULT_LOG_STRING, line_index, "FOUND TOO MANY RESULT FOR %s with %s =>   [ %d ]" % (toString(
                    self.target_model), toString(search_criteria), len(found)))
                return
            else:
                currentObj = None

        # Traitement des suppressions ou archivages
        if TO_BE_ARCHIVED and CAN_BE_ARCHIVED:
            if not currentObj == None:
                currentObj.write({'active': False})
                currentObj.active = False
                self.odooenv.cr.commit()
            return

        # Attention, il y a des champs collection ou relationnels
        if len(self.o2mFields) > 0 or len(self.m2oFields) > 0:
            stdRow = {}
            for f in self.stdFields:
                if f in data_values:
                    stdRow[f] = data_values[f]

            # Many To One Fields, might be mandatory, so needs to be treated first and added to StdRow
            for f in self.m2oFields.keys():

                if f in data_values:
                    field = self.m2oFields[f]
                    # reference Many2One,
                    if field[0] == 0 and data_values[f] and len(data_values[f]) > 0:
                        cond = []
                        if len(field) > 4:
                            cond = ['&', (field[3], '=', data_values[f]), field[4]]
                        else:
                            cond = [(field[3], '=', data_values[f])]

                        vals = self.odooenv[field[2]].search(cond, limit=1)

                        if len(vals) == 1:
                            stdRow[field[1]] = vals[0].id
                        else:
                            self.logger.warning(DEFAULT_LOG_STRING, line_index, " found  %d  values for %s unable to reference %s - %s " % (
                                                len(vals), toString(data_values[f]), toString(field[3]), toString(vals)))

            # Create Object if it does not yet exist, else, write updates
            try:
                if currentObj == None:
                    currentObj = self.target_model.create(self.map_values(stdRow))
                else:
                    currentObj.write(self.map_values(stdRow))

                self.odooenv.cr.commit()
            except ValueError as e:
                self.odooenv.cr.rollback()
                self.logger.error(DEFAULT_LOG_STRING, line_index, " wrong values where creating/updating object: %s  -> %s [ %s ]" % (
                                  self.target_model, toString(stdRow), toString(currentObj)))
                self.logger.error("                    MSG: {0}".format(toString(e)))
                currentObj = None
            except Exception as e:
                self.odooenv.cr.rollback()
                self.logger.error(DEFAULT_LOG_STRING + " Generic Error : " + toString(type(e)) + "--- " + toString(e))
                currentObj = None

            # One2Many Fields,

            try:
                for f in self.o2mFields.keys():
                    if f in data_values:
                        members = data_values[f].split(';')
                        field = self.o2mFields[f]
                        if len(members) > 0 and currentObj != None:
                            if field[0] == 1:
                                currentObj.write({field[1]: [(5, False, False)]})
                            for m in members:
                                if len(m) > 0:
                                    # For adding some stuffs in lists do : https://www.odoo.com/documentation/10.0/reference/orm.html#odoo.models.Model.write
                                    # References records in  One2Many
                                    if field[0] == 0:
                                        vals = self.odooenv[field[2]].search([(field[3], '=', m)], limit=1)
                                        if len(vals) == 1:
                                            currentObj.write({field[1]: [(4, vals[0].id, False)]})
                                        else:
                                            self.logger.warning(
                                                DEFAULT_LOG_STRING, line_index, "found %d  values for %s,  unable to reference" % (len(vals), toString(m)))

                                    # Creates records in  One2Many
                                    elif field[0] == 1:
                                        values = eval(m)
                                        currentObj.write({field[1]: [(0, False, values)]})
                self.odooenv.cr.commit()
            except ValueError as e:
                self.odooenv.cr.rollback()
                self.logger.error(DEFAULT_LOG_STRING, line_index, " Wrong values where updating object: %s -> %s " % (
                                  str(self.target_model), toString(stdRow)))
                self.logger.error("                    MSG: %s", toString(e))
                currentObj = None
            except Exception as e:
                self.odooenv.cr.rollback()
                self.logger.error(DEFAULT_LOG_STRING + " Generic Error : " + toString(type(e)) + "--- " + toString(e))
                currentObj = None

            self.odooenv.cr.commit()

        # pas de champs collection
        else:

            try:
                if currentObj == None:
                    currentObj = self.target_model.create(self.map_values(data_values))
                else:
                    currentObj.write(self.map_values(data_values))
                self.odooenv.cr.commit()
            except ValueError as e:
                self.odooenv.cr.rollback()
                self.logger.error(DEFAULT_LOG_STRING, line_index, " error where creating/updating object: %s --> %s [%s]" % (
                    str(self.target_model), toString(data_values), toString(currentObj)))
                self.logger.error("                    MSG: {0}".format(toString(e)))
            except Exception as e:
                self.odooenv.cr.rollback()
                self.logger.error(DEFAULT_LOG_STRING, line_index, " Generic Error : %s --- %s" %
                                  (toString(type(e)), toString(e)))
                currentObj = None

        # *****

        # Finally commit
        self.odooenv.cr.commit()

    #-------------------------------------------------------------------------------------
    def get_book(self, import_file):
        if self.fileType == FILE_TYPE_CSV:
            return CSVImporterMixin._open_csv(self, import_file, asDict=True)
        else:
            return XLImporterBaseProcessor.get_book(self, import_file)

    #-------------------------------------------------------------------------------------
    def get_tabs(self, import_file=None):
        if self.fileType == FILE_TYPE_CSV:
            yield ('csv file', self.book)
        else:
            for tab in XLImporterBaseProcessor.get_tabs(self, import_file):
                yield tab

#-------------------------------------------------------------------------------------
    def get_rows(self, tab=None):
        if self.fileType == FILE_TYPE_CSV:
            #firstline in header
            idx = 0
            yield (0, tab[1].fieldnames)
            for row in tab[1]:
                idx += 1
                yield (idx, row)
        else:
            for row in XLImporterBaseProcessor.get_rows(self, tab):
                yield (0, row)
                idx += 1

    #-------------------------------------------------------------------------------------
    # Provides a dictionary of values in a row
    def get_row_values_as_dict(self, tab=None, row=None, tabheader=None):

        values = None
        if self.fileType == FILE_TYPE_CSV:
            values = CSVImporterMixin.get_row_values_as_dict(self, tab, row, tabheader)
        else:
            values = XLImporterBaseProcessor.get_row_values_as_dict(self, tab, row, tabheader)

        return values

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file, force=False):
        ext = import_file.filename.split('.')[-1]
        if (ext in AUTHORIZED_EXTS):
            if ext == 'csv':
                self.fileType = FILE_TYPE_CSV
            else:
                self.fileType = FILE_TYPE_XL

            MultiSheetLineIterator.process_file(self, import_file, force)
        else:
            self.logger.error("Cannot process file: Wrong extension -> %s", ext)
            self.end_processing(import_file, success=False, status='failure', any_message="Wrong file exension")

    #-------------------------------------------------------------------------------------
