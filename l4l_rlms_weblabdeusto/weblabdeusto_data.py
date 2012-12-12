#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 onwards University of Deusto
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# This software consists of contributions made by many individuals,
# listed below:
#
# Author: Pablo Orduña <pablo@ordunya.com>
#

import re
import os
import base64

class CoordException(Exception): pass

CoordInvalidAddressParams = CoordException
CoordInvalidLevelAddress  = CoordException 
CoordInvalidAddressName   = CoordException

class SessionInvalidSessionIdError(Exception): pass

class CoordAddress(object):
    FORMAT = '%(server)s:%(instance)s@%(machine)s'
    REGEX_FORMAT = '^' + FORMAT % {
        'server' : '(.*)',
        'instance' : '(.*)',
        'machine' : '(.*)'
    } + '$'

    def __init__(self,machine_id,instance_id='',server_id=''):
        """ CoordAddress(machine_id,instance_id,server_id) -> CoordAddress

        CoordAddress is the relative address for a server in the CoordinationMap.
        Fields:
            * machine_id
            * instance_id
            * server_id
            * address (an address converted to string
                with CoordAddress.FORMAT format)

        Just in the same way networks ending are represented ending with 0s,
        the CoordAddresses with server field empty are the address for an
        instance, and the CoordAddresses with server and instances fields
        empty are the addresses for machines.
        """
        if not type(machine_id) in (str,unicode) or machine_id == '':
            raise CoordInvalidAddressParams( "%s: not a valid machine_id" % machine_id)
        if not type(instance_id) in (str,unicode):
            raise CoordInvalidAddressParams( "%s: not a valid instance_id" % instance_id)
        if not type(server_id) in (str,unicode):
            raise CoordInvalidAddressParams( "%s: not a valid server_id" % server_id)
        if instance_id == '' and server_id != '':
            raise CoordInvalidAddressParams( "%s, %s: not valid parameters" % (instance_id, server_id))

        self.machine_id = machine_id
        self.instance_id = instance_id
        self.server_id = server_id

        self._reload_address()

    def _reload_address(self):
        self._address = CoordAddress.FORMAT % {
                'server'    : self.server_id,
                'instance'  : self.instance_id,
                'machine'   : self.machine_id
            }

    @property
    def address(self):
        return self._address

    # is_* methods
    def is_server(self):
        return self.server_id != ''

    def is_instance(self):
        return self.server_id == '' and self.instance_id != ''

    def is_machine(self):
        return self.server_id == '' and self.instance_id == ''

    # get_* methods
    def get_instance_address(self):
        if not self.is_server():
            raise CoordInvalidLevelAddress( '%s: not a server_address' % self)
        new_addr = self.copy()
        new_addr.server_id = ''
        new_addr._reload_address()
        return new_addr

    def get_machine_address(self):
        if not self.is_server() and not self.is_instance():
            raise CoordInvalidLevelAddress( '%s: not a server or instance address' % self)
        new_addr = self.copy()
        new_addr.server_id = new_addr.instance_id = ''
        new_addr._reload_address()
        return new_addr

    # deep copy method

    def copy(self):
        return CoordAddress(
                self.machine_id,
                self.instance_id,
                self.server_id
            )

    # factory in order to create new CoordAddresses

    @staticmethod
    def translate_address(address):
        """ translate_address(address) -> CoordAddress

        Given a Coordinator Address in CoordAddress.FORMAT format,
        translate_address will provide the corresponding CoordAddress
        """
        try:
            m = re.match(CoordAddress.REGEX_FORMAT,address)
        except TypeError:
            raise CoordInvalidAddressName(
                "%(address)s is not a valid address. Format: %(format)s" % {
                "address" : address,
                "format"  : CoordAddress.FORMAT
            }
            )
        if m is None:
            raise CoordInvalidAddressName(
                    '%(address)s is not a valid address. Format: %(format)s' % {
                        'address' : address,
                        'format'  : CoordAddress.FORMAT
                    })
        else:
            server,instance,machine = m.groups()
            return CoordAddress(machine,instance,server)

    # Auxiliar methods

    def __cmp__(self,other):
        if other is None:
            return cmp(self.address,None)
        else:
            if isinstance(other,CoordAddress):
                return cmp(self.address,other.address)
            else:
                return cmp(self.address,None)

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return '%(name)s <%(address)s>' % {
            'name'      : self.__class__.__name__,
            'address'   : self.address
        }

    def __repr__(self):
        return 'CoordAddress(%r, %r, %r)' % (
            self.machine_id, self.instance_id, self.server_id )

    def __hash__(self):
        return hash(self.address) + 1

class SessionId(object):
    def __init__(self, real_id):
        if not isinstance(real_id,basestring):
            raise SessionInvalidSessionIdError( "Not a string: %s" % real_id )

        self.id = real_id

    def __cmp__(self, other):
        if isinstance(other,SessionId):
            return cmp(self.id,other.id)
        else:
            try:
                return cmp(hash(self.id),hash(other))
            except TypeError:
                return 1

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return "SessionId(%r)" % self.id

    def __str__(self):
        return "Session ID: '%s'" % self.id

NULL_POSITION = 100000

class InvalidReservationStatusError(Exception):
    pass

class Reservation(object):

    WAITING              = "Reservation::waiting"
    WAITING_CONFIRMATION = "Reservation::waiting_confirmation"
    WAITING_INSTANCES    = "Reservation::waiting_instances"
    CONFIRMED            = "Reservation::confirmed"
    POST_RESERVATION     = "Reservation::post_reservation"

    POLLING_STATUS = (WAITING, WAITING_CONFIRMATION, WAITING_INSTANCES, CONFIRMED)

    def __init__(self, status, reservation_id):
        """ __init__(status, reservation_id)

        status is Reservation.WAITING, Reservation.CONFIRMED, etc.
        reservation_id is the reservation identifier, used to interact with the experiment
        """
        super(Reservation,self).__init__()
        self.status         = status
        self.reservation_id = SessionId(reservation_id)

    def __repr__(self):
        return self.status

    @staticmethod
    def translate_reservation_from_data(status_text, reservation_id, position, time, initial_configuration, end_data, url, finished, initial_data, remote_reservation_id):
        if status_text == Reservation.WAITING:
            reservation = WaitingReservation(reservation_id, position)
        elif status_text == Reservation.WAITING_CONFIRMATION:
            reservation = WaitingConfirmationReservation(reservation_id, url)
        elif status_text == Reservation.WAITING_INSTANCES:
            reservation = WaitingInstances(reservation_id, position)
        elif status_text == Reservation.CONFIRMED:
            reservation = ConfirmedReservation(reservation_id, time, initial_configuration, url, remote_reservation_id)
        elif status_text == Reservation.POST_RESERVATION:
            reservation = PostReservationReservation(reservation_id, finished, initial_data, end_data)
        else:
            raise InvalidReservationStatusError("Invalid reservation status_text: '%s'." % ( status_text ) )
        return reservation

    # XXX TODO: a new state would be required, but I don't have to deal with that
    def is_null(self):
        return isinstance(self, WaitingInstances) and self.position == NULL_POSITION


class WaitingReservation(Reservation):
    def __init__(self, reservation_id, position):
        super(WaitingReservation,self).__init__(Reservation.WAITING, reservation_id)
        self.position = position

    def __repr__(self):
        return "WaitingReservation(reservation_id = %r, position = %r)" % (self.reservation_id.id, self.position)


class ConfirmedReservation(Reservation):
    def __init__(self, reservation_id, time, initial_configuration, url, remote_reservation_id):
        super(ConfirmedReservation,self).__init__(Reservation.CONFIRMED, reservation_id)
        self.time                  = time
        self.initial_configuration = initial_configuration
        self.url                   = url
        self.remote_reservation_id = SessionId(remote_reservation_id)

    def __repr__(self):
        return "ConfirmedReservation(reservation_id = %r, time = %r, initial_configuration = %r, url = %r, remote_reservation_id = %r)" % (self.reservation_id.id, self.time, self.initial_configuration, self.url, self.remote_reservation_id.id)

class WaitingConfirmationReservation(Reservation):
    def __init__(self, reservation_id, url):
        super(WaitingConfirmationReservation,self).__init__(Reservation.WAITING_CONFIRMATION, reservation_id)
        self.url = url

    def __repr__(self):
        return "WaitingConfirmationReservation(reservation_id = %r, url = %r)" % (self.reservation_id.id, self.url)


class WaitingInstances(Reservation):
    def __init__(self, reservation_id, position):
        super(WaitingInstances,self).__init__(Reservation.WAITING_INSTANCES, reservation_id)
        self.position = position

    def __repr__(self):
        return "WaitingInstances(reservation_id = %r, position = %r)" % (self.reservation_id.id, self.position)


class NullReservation(WaitingInstances):
    def __init__(self):
        super(NullReservation, self).__init__('null reservation', NULL_POSITION)

class PostReservationReservation(Reservation):
    def __init__(self, reservation_id, finished, initial_data, end_data):
        super(PostReservationReservation,self).__init__(Reservation.POST_RESERVATION, reservation_id)
        self.finished     = finished
        self.initial_data = initial_data
        self.end_data     = end_data

    def __repr__(self):
        return "PostReservationReservation(reservation_id = %r, finished = %r, initial_data = %r, end_data = %r)" % (self.reservation_id.id, self.finished, self.initial_data, self.end_data)

class Command(object):

    def __init__(self, commandstring):
        self.commandstring = commandstring

    def get_command_string(self):
        return self.commandstring

    def __cmp__(self, other):
        if isinstance(other, Command):
            return cmp(self.commandstring, other.commandstring)
        return -1

    def to_dict(self):
        return {'commandstring': self.commandstring}

class NullCommand(Command):

    def __init__(self):
        super(NullCommand, self).__init__(None)


class ExperimentId(object):

    def __init__(self, exp_name, cat_name):
        self.exp_name  = unicode(exp_name)
        self.cat_name  = unicode(cat_name)

    def __cmp__(self, other):
        if isinstance(other, ExperimentId):
            return -1
        if self.exp_name != other.exp_name:
            return cmp(self.exp_name, other.exp_name)

        return cmp(self.cat_name, other.cat_name)

    def to_dict(self):
        return {'exp_name': self.exp_name, 'cat_name': self.cat_name}

    def to_weblab_str(self):
        return '%s@%s' % (self.exp_name, self.cat_name)

    @staticmethod
    def parse(weblab_str):
        pos = weblab_str.find("@")
        experiment_name = weblab_str[:pos]
        category_name   = weblab_str[pos + 1 :]
        return ExperimentId(experiment_name, category_name)

class ExperimentInstanceId(object):

    def __init__(self, inst_name, exp_name, cat_name):
        self.inst_name = unicode(inst_name)
        self.exp_name  = unicode(exp_name)
        self.cat_name  = unicode(cat_name)

    def to_experiment_id(self):
        return ExperimentId(self.exp_name, self.cat_name)

    def to_weblab_str(self):
        return "%s:%s@%s" % (self.inst_name, self.exp_name, self.cat_name)

    def __cmp__(self, other):
        return cmp(str(self), str(other))

    def __hash__(self):
        return hash(self.inst_name) * 31 ** 3 + hash(self.exp_name) * 31 ** 2 + hash(self.cat_name) * 31 + hash("ExperimentInstanceId")

class CommandSent(object):

    def __init__(self, command, timestamp_before, response = None, timestamp_after = None):
        self.command          = command          # Command
        self.timestamp_before = timestamp_before # seconds.millis since 1970 in GMT
        if response == None:
            self.response = Command.NullCommand()
        else:
            self.response = response
        self.timestamp_after = timestamp_after

class LoadedFileSent(object):

    def __init__(self, file_content, timestamp_before, response, timestamp_after, file_info):
        self.file_content     = file_content
        self.timestamp_before = timestamp_before
        self.response         = response
        self.timestamp_after  = timestamp_after
        self.file_info        = file_info

    # Just in case
    def load(self):
        return self

class FileSent(object):

    def __init__(self, file_path, file_hash, timestamp_before, response = None, timestamp_after = None, file_info = None):
        self.file_path        = file_path
        self.file_hash        = file_hash
        self.file_info        = file_info
        self.timestamp_before = timestamp_before
        if response == None:
            self.response = Command.NullCommand()
        else:
            self.response = response
        self.timestamp_after  = timestamp_after

    def load(self, storage_path):
        content = base64.encodestring(open(os.sep.join((storage_path, self.file_path)), 'rb').read())
        return LoadedFileSent(content, self.timestamp_before, self.response, self.timestamp_after, self.file_info)

class ExperimentUsage(object):

    def __init__(self, experiment_use_id = None, start_date = None, end_date = None, from_ip = u"unknown", experiment_id = None, reservation_id = None, coord_address = None, request_info = None, commands = None, sent_files = None):
        self.experiment_use_id      = experiment_use_id # int
        self.start_date             = start_date        # seconds.millis since 1970 in GMT
        self.end_date               = end_date          # seconds.millis since 1970 in GMT
        self.from_ip                = from_ip
        self.experiment_id          = experiment_id     # weblab.data.experiments.ExperimentId
        self.reservation_id         = reservation_id    # string, the reservation identifier
        self.coord_address          = coord_address     # voodoo.gen.coordinator.CoordAddress.CoordAddress
        if request_info is None:
            self.request_info       = {}
        else:
            self.request_info       = request_info

        if commands is None:
            self.commands           = []   # [CommandSent]
        else:
            self.commands           = commands

        if sent_files is None:
            self.sent_files         = []   # [FileSent]
        else:
            self.sent_files         = sent_files

    def append_command(self, command_sent):
        """
        append_command(command_sent)
        Appends the specified command to the local list of commands,
        so that later the commands that were sent during the session
        can be retrieved for logging or other purposes.

        @param command_sent The command that was just sent, which we will register
        @return The index of the command we just added in the internal list. Mostly,
        for identification purposes.
        """
        # isinstance(command_sent, CommandSent)
        self.commands.append(command_sent)
        return len(self.commands) - 1

    def update_command(self, command_id, command_sent):
        self.commands[command_id] = command_sent

    def append_file(self, file_sent):
        self.sent_files.append(file_sent)
        return len(self.sent_files) - 1

    def update_file(self, file_id, file_sent):
        self.sent_files[file_id] = file_sent

    def load_files(self, path):
        loaded_sent_files = []
        for sent_file in self.sent_files:
            loaded_sent_file = sent_file.load(path)
            loaded_sent_files.append(loaded_sent_file)
        self.sent_files = loaded_sent_files
        return self

class ReservationResult(object):

    ALIVE     = 'alive'
    CANCELLED = 'cancelled'
    FINISHED  = 'finished'
    FORBIDDEN = 'forbidden'

    def __init__(self, status):
        self.status = status

    def is_alive(self):
        return False

    def is_finished(self):
        return False

    def is_cancelled(self):
        return False

    def is_forbidden(self):
        return False

class AliveReservationResult(ReservationResult):

    def __init__(self, running):
        super(AliveReservationResult, self).__init__(ReservationResult.ALIVE)
        self.running = running
        self.waiting = not running

    def is_alive(self):
        return True

class RunningReservationResult(AliveReservationResult):

    def __init__(self):
        super(RunningReservationResult, self).__init__(True)

class WaitingReservationResult(AliveReservationResult):

    def __init__(self):
        super(WaitingReservationResult, self).__init__(True)

class CancelledReservationResult(ReservationResult):

    def __init__(self):
        super(CancelledReservationResult, self).__init__(ReservationResult.CANCELLED)

    def is_cancelled(self):
        return True

class ForbiddenReservationResult(ReservationResult):

    def __init__(self):
        super(ForbiddenReservationResult, self).__init__(ReservationResult.FORBIDDEN)

    def is_forbidden(self):
        return True

class FinishedReservationResult(ReservationResult):

    def __init__(self, experiment_use):
        super(FinishedReservationResult, self).__init__(ReservationResult.FINISHED)
        self.experiment_use = experiment_use

    def is_finished(self):
        return True

