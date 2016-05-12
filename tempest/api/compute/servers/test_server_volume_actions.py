# Copyright 2016 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from six.moves.urllib import parse as urlparse
import testtools

from tempest.api.compute import base
from tempest.common import compute
from tempest.common.utils import data_utils
from tempest.common.utils.linux import remote_client
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class ServerVolumeActionsTestJSON(base.BaseV2ComputeTest):
    run_ssh = CONF.validation.run_validation

    def setUp(self):
        server = self.create_test_server(volume_backed=True,
                                         wait_until='ACTIVE')
        self.__class__.server_id = server['id']

    def tearDown(self):
        self.server_check_teardown()
        super(ServerActionsTestJSON, self).tearDown()

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServerActionsTestJSON, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServerActionsTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        cls.set_validation_resources()

        super(ServerActionsTestJSON, cls).resource_setup()
        cls.server_id = cls.rebuild_server(None, validatable=True)

    @test.idempotent_id('79f058fa-e178-4d6d-8019-6708afabe9eb')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize is not available.')
    @test.services('compute', 'volume')
    def test_resize_volume_backed_server_revert(self):
        # We create an instance for use in this test
        resize_flavor = CONF.compute.flavor_ref_alt
        LOG.debug("Resizing instance %s from flavor %s to flavor %s",
                  server['id'], server['flavor']['id'], resize_flavor)
        self.servers_client.resize_server(server_id, resize_flavor)
        waiters.wait_for_server_status(self.servers_client, server_id,
                                       'VERIFY_RESIZE')

        LOG.debug("Reverting resize of instance %s", server_id)
        self.servers_client.revert_resize_server(server_id)

        waiters.wait_for_server_status(self.servers_client, server_id,
                                       'ACTIVE')
