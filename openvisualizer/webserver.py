#!/usr/bin/python
# Copyright (c) 2013, Ken Bannister.
# All rights reserved.
#
# Released under the BSD 2-Clause license as published at the link below.
# http://opensource.org/licenses/BSD-2-Clause
import datetime
import functools
import logging
import re
import xmlrpclib

import bottle

from openvisualizer import VERSION
from openvisualizer.bspemulator import vcdlogger
from openvisualizer.eventbus.eventbusclient import EventBusClient
from openvisualizer.simengine import simengine

log = logging.getLogger('OVWebServer')

# add default parameters to all bottle templates
bottle.view = functools.partial(bottle.view, ovVersion='.'.join(list([str(v) for v in VERSION])))


class WebServer(EventBusClient):
    """ Provides web UI for OpenVisualizer. Runs as a webapp in a Bottle web server. """

    def __init__(self, web_srv, rpc_server_addr):
        """
        :param web_srv: Web server
        """
        log.debug('create instance')

        # store params
        self.rpc_server = xmlrpclib.ServerProxy('http://{}:{}'.format(*rpc_server_addr))
        self.engine = simengine.SimEngine()
        self.web_srv = web_srv

        # initialize parent classes
        super(WebServer, self).__init__(name='OpenVisualizerWeb', registrations=[])

        self._define_routes()
        # To find page templates
        bottle.TEMPLATE_PATH.append('openvisualizer/web_files/templates/')

        # Set DAGroots imported
        # if app.dagroot_list:
        #     # Wait the end of the mote threads creation
        #     time.sleep(1)
        #     for mote_id in app.dagroot_list:
        #         self._show_moteview(mote_id)
        #         self._get_mote_data(mote_id)
        #         self._toggle_dagroot(mote_id)

    # ======================== public ==========================================

    # ======================== private =========================================

    def _define_routes(self):
        """
        Matches web URL to impelementing method. Cannot use @route annotations on the methods due to the class-based
        implementation.
        """
        self.web_srv.route(path='/', callback=self._show_moteview)
        self.web_srv.route(path='/moteview', callback=self._show_moteview)
        self.web_srv.route(path='/moteview/:moteid', callback=self._show_moteview)
        self.web_srv.route(path='/motedata/:moteid', callback=self._get_mote_data)
        self.web_srv.route(path='/toggleDAGroot/:moteid', callback=self._toggle_dagroot)
        self.web_srv.route(path='/eventBus', callback=self._show_event_bus)
        self.web_srv.route(path='/routing', callback=self._show_routing)
        self.web_srv.route(path='/routing/dag', callback=self._show_dag)
        self.web_srv.route(path='/connectivity', callback=self._show_connectivity)
        self.web_srv.route(path='/connectivity/motes', callback=self._show_motes_connectivity)
        self.web_srv.route(path='/eventdata', callback=self._get_event_data)
        self.web_srv.route(path='/wiresharkDebug/:enabled', callback=self._set_wireshark_debug)
        self.web_srv.route(path='/gologicDebug/:enabled', callback=self._set_gologic_debug)
        self.web_srv.route(path='/topology', callback=self._topology_page)
        self.web_srv.route(path='/topology/data', callback=self._topology_data)
        self.web_srv.route(path='/topology/download', callback=self._topology_download)
        self.web_srv.route(path='/topology/motes', method='POST', callback=self._topology_motes_update)
        self.web_srv.route(path='/topology/connections', method='PUT', callback=self._topology_connections_create)
        self.web_srv.route(path='/topology/connections', method='POST', callback=self._topology_connections_update)
        self.web_srv.route(path='/topology/connections', method='DELETE', callback=self._topology_connections_delete)
        self.web_srv.route(path='/topology/route', method='GET', callback=self._topology_route_retrieve)
        self.web_srv.route(path='/static/<filepath:path>', callback=self._server_static)

    @bottle.view('moteview.tmpl')
    def _show_moteview(self, moteid=None):
        """
        Collects the list of motes, and the requested mote to view.
        :param moteid: 16-bit ID of mote (optional)
        """
        if log.isEnabledFor(logging.DEBUG):
            log.debug("moteview moteid parameter is {0}".format(moteid))

        mote_list = self.rpc_server.get_mote_dict().keys()

        tmpl_data = {
            'motelist': mote_list,
            'requested_mote': moteid if moteid else 'none',
        }
        return tmpl_data

    def _server_static(self, filepath):
        return bottle.static_file(filepath, root='openvisualizer/web_files/static/')

    def _toggle_dagroot(self, moteid):
        """
        Triggers toggle DAGroot state, via MoteState. No real response. Page is updated when next retrieve mote data.
        :param moteid: 16-bit ID of mote
        """

        log.debug('Toggle root status for moteid {0}'.format(moteid))
        try:
            ms = self.rpc_server.get_mote_state(moteid)
        except xmlrpclib.Fault as err:
            log.error("A fault occurred: {}".format(err))
            return '{"result" : "fail"}'

        if ms:
            if log.isEnabledFor(logging.DEBUG):
                log.debug('Found mote {0} in mote_states'.format(moteid))
            self.rpc_server.set_root(moteid)
            return '{"result" : "success"}'
        else:
            if log.isEnabledFor(logging.DEBUG):
                log.debug('Mote {0} not found in mote_states'.format(moteid))
            return '{"result" : "fail"}'

    def _get_mote_data(self, moteid):
        """
        Collects data for the provided mote.
        :param moteid: 16-bit ID of mote
        """
        states = {}

        if log.isEnabledFor(logging.DEBUG):
            log.debug('Get JSON data for moteid {0}'.format(moteid))
        try:
            states = self.rpc_server.get_mote_state(moteid)
        except xmlrpclib.Fault as err:
            log.error("Could not fetch mote state for mote {}: {}".format(moteid, err))
            return states
        if log.isEnabledFor(logging.DEBUG):
            log.debug('Found mote {0} in mote_states'.format(moteid))
        return states

    def _set_wireshark_debug(self, enabled):
        """
        Selects whether eventBus must export debug packets.
        :param enabled: 'true' if enabled; any other value considered false
        """
        log.info('Enable wireshark debug : {0}'.format(enabled))
        # self.app.ebm.set_wireshark_debug(enabled == 'true')
        return '{"result" : "success"}'

    def _set_gologic_debug(self, enabled):
        log.info('Enable GoLogic debug : {0}'.format(enabled))
        vcdlogger.VcdLogger().set_enabled(enabled == 'true')
        return '{"result" : "success"}'

    @bottle.view('eventBus.tmpl')
    def _show_event_bus(self):
        """ Simple page; data for the page template is identical to the data for periodic updates of event list. """
        tmpl_data = self._get_event_data().copy()
        return tmpl_data

    def _show_dag(self):
        states, edges = self.rpc_server.get_dag()
        return {'states': states, 'edges': edges}

    @bottle.view('connectivity.tmpl')
    def _show_connectivity(self):
        return {}

    def _show_motes_connectivity(self):
        states, edges = self.rpc_server.get_motes_connectivity()
        return {'states': states, 'edges': edges}

    @bottle.view('routing.tmpl')
    def _show_routing(self):
        return {}

    @bottle.view('topology.tmpl')
    def _topology_page(self):
        """ Retrieve the HTML/JS page. """
        return {}

    def _topology_data(self):
        """ Retrieve the topology data, in JSON format. """

        motes = []
        rank = 0
        while True:
            try:
                mh = self.engine.get_mote_handler(rank)
                mote_id = mh.get_id()
                (lat, lon) = mh.get_location()
                motes += [{'id': mote_id, 'lat': lat, 'lon': lon}]
                rank += 1
            except IndexError:
                break

        # connections
        connections = self.engine.propagation.retrieve_connections()

        data = {'motes': motes, 'connections': connections}

        return data

    def _topology_motes_update(self):

        motes_temp = {}
        for (k, v) in bottle.request.forms.items():
            m = re.match("motes\[(\w+)\]\[(\w+)\]", k)

            assert m
            index = int(m.group(1))
            param = m.group(2)
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
            if index not in motes_temp:
                motes_temp[index] = {}
            motes_temp[index][param] = v

        for (_, v) in motes_temp.items():
            mh = self.engine.get_mote_handler_by_id(v['id'])
            mh.set_location(v['lat'], v['lon'])

    def _topology_connections_create(self):

        data = bottle.request.forms
        assert sorted(data.keys()) == sorted(['fromMote', 'toMote'])

        from_mote = int(data['fromMote'])
        to_mote = int(data['toMote'])

        self.engine.propagation.create_connection(from_mote, to_mote)

    def _topology_connections_update(self):
        data = bottle.request.forms
        assert sorted(data.keys()) == sorted(['fromMote', 'toMote', 'pdr'])

        from_mote = int(data['fromMote'])
        to_mote = int(data['toMote'])
        pdr = float(data['pdr'])

        self.engine.propagation.update_connection(from_mote, to_mote, pdr)

    def _topology_connections_delete(self):

        data = bottle.request.forms
        assert sorted(data.keys()) == sorted(['fromMote', 'toMote'])

        from_mote = int(data['fromMote'])
        to_mote = int(data['toMote'])

        self.engine.propagation.delete_connection(from_mote, to_mote)

    def _topology_route_retrieve(self):

        data = bottle.request.query
        assert data.keys() == ['destination']

        destination_eui = [0x14, 0x15, 0x92, 0xcc, 0x00, 0x00, 0x00, int(data['destination'])]

        route = self._dispatch_and_get_result(signal='getSourceRoute', data=destination_eui)
        route = [r[-1] for r in route]
        data = {'route': route}

        return data

    def _topology_download(self):
        """ Retrieve the topology data, in JSON format, and download it. """
        data = self._topology_data()
        now = datetime.datetime.now()

        dagroot = self.rpc_server.get_dagroot()
        if dagroot is not None:
            dagroot = ''.join('%02x' % b for b in dagroot)

        data['DAGroot'] = dagroot

        bottle.response.headers['Content-disposition'] = 'attachment; filename=topology_data_' + now.strftime(
            "%d-%m-%y_%Hh%M") + '.json'
        bottle.response.headers['filename'] = 'test.json'
        bottle.response.headers['Content-type'] = 'application/json'

        return data

    def _get_event_data(self):
        res = {
            'isDebugPkts': 'true' if self.rpc_server.get_ebm_wireshark_enabled() else 'false',
            'stats': self.rpc_server.get_ebm_stats()
        }
        return res
