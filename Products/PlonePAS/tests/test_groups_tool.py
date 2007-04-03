##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
"""

import os, sys
import unittest

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(sys.argv[0]), 'framework.py'))

from PlonePASTestCase import PlonePASTestCase
from Testing.ZopeTestCase import user_name

from zope.component import getUtility

from cStringIO import StringIO
from zExceptions import BadRequest
from Acquisition import aq_base, aq_inner, aq_parent
from AccessControl import Permissions
from AccessControl import Unauthorized

from Products.PlonePAS.interfaces.group import IGroupTool
from Products.PlonePAS.interfaces.group import IGroupDataTool
from Products.PlonePAS.tools.groupdata import GroupData
from Products.PlonePAS.plugins.group import PloneGroup

class GroupsToolTest(PlonePASTestCase):

    def afterSetUp(self):
        self.gt = gt = getUtility(IGroupTool)
        self.gd = gd = getUtility(IGroupDataTool)

        self.group_id = 'group1'
        # Create a new Group
        self.loginAsPortalOwner()
        gt.addGroup(self.group_id, ['Reviewer'], [],
                    {'email': 'group1@host.com',
                     'title': 'Group #1'})

    def test_get_group(self):
        # Use PAS (monkeypatched) API method to get a group by id.
        group = self.portal.acl_users.getGroup(self.group_id)
        self.failIf(group is None)

        # Should be wrapped into the GroupManagement, which is wrapped
        # into the PAS.
        got = aq_base(aq_parent(aq_parent(group)))
        expected = aq_base(self.portal.acl_users)
        self.assertEquals(got, expected)

        self.failUnless(isinstance(group, PloneGroup))

    def test_get_group_by_id(self):
        # Use tool way of getting group by id. This returns a
        # GroupData object wrapped by the group
        group = self.gt.getGroupById(self.group_id)
        self.failIf(group is None)
        self.failUnless(isinstance(group, GroupData))
        self.failUnless(isinstance(aq_parent(group), PloneGroup))

class GroupWorkspacesTest(PlonePASTestCase):

    def afterSetUp(self):
        self.gt = gt = getUtility(IGroupTool)
        self.gd = gd = getUtility(IGroupDataTool)
        # Enable group-area creation
        self.gt.groupWorkspacesCreationFlag = 1
        # Those are all valid chars in Zope.
        self.gid = "Group #1 - Houston, TX. ($100)"
        self.loginAsPortalOwner()

    def test_funky_group_ids_1(self):
        gid = self.gid
        ginfo = (gid, ['Reviewer'], [],
                 {'email': 'group1@host.com',
                  'title': 'Group #1'})
        # Create a new Group
        self.gt.addGroup(*ginfo)

    def test_funky_group_ids_2(self):
        # Forward-slash is not allowed
        gid = self.gid + '/'
        ginfo = (gid, ['Reviewer'], [],
                 {'email': 'group1@host.com',
                  'title': 'Group #1'})
        # Create a new Group
        self.failUnlessRaises(BadRequest, self.gt.addGroup, *ginfo)

class TestMethodProtection(PlonePASTestCase):
    # GroupData has wrong security declarations

    def afterSetUp(self):
        self.groups = self.portal.portal_groups
        self.groups.groupWorkspacesCreationFlag = 0
        self.groups.addGroup('foo')
        self.groupdata = self.groups.getGroupById('foo')

    def testAnonAddMember(self):
        self.logout()
        self.assertRaises(Unauthorized, self.groupdata.addMember, user_name)

    def testAnonRemoveMember(self):
        self.logout()
        self.assertRaises(Unauthorized, self.groupdata.removeMember, user_name)

    def testMemberAddMember(self):
        self.assertRaises(Unauthorized, self.groupdata.addMember, user_name)

    def testMemberRemoveMember(self):
        self.assertRaises(Unauthorized, self.groupdata.removeMember, user_name)

    def testManagerAddMember(self):
        self.setPermissions([Permissions.manage_users])
        self.groupdata.addMember(user_name)

    def testManagerRemoveMember(self):
        self.setPermissions([Permissions.manage_users])
        self.groupdata.addMember(user_name)
        self.groupdata.removeMember(user_name)



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(GroupsToolTest))
    suite.addTest(unittest.makeSuite(GroupWorkspacesTest))
    suite.addTest(unittest.makeSuite(TestMethodProtection))
    return suite

if __name__ == '__main__':
    framework()
