#
#
import time
from unittest import TestCase
import ansar.create as ar
import ansar.create.point as pt
import ansar.create.timing as tm

from support import *

__all__ = [
    'TestDbInternetDevice',
]

#
#
class Person(object):
    def __init__(self, name=None, home=None, account=None):
        self.name = name
        self.home = home or ar.make(ar.ArrayOf(ar.Float8, 2))
        self.account = account

PERSON_SCHEMA = {'name': ar.Unicode, 'home': ar.ArrayOf(ar.Float8, 2), 'account': ar.Unicode}

ar.bind(Person, object_schema=PERSON_SCHEMA)

DEFAULT = {}     # Default.

# Prime it.
DEFAULT['errol'] = Person(name='errol', home=[-39.89839804139349, 175.06452769630488], account='1042-228899-023')
DEFAULT['hortense'] = Person(name='hortense', home=[-39.9095590228883, 175.062124846032], account='1042-228629-023')
DEFAULT['gertrude'] = Person(name='gertrude', home=[-39.94482954896937, 174.986107480598], account='1042-071899-023')
DEFAULT['annabel'] = Person(name='annabel', home=[-39.76921060510792, 174.62750969461968], account='1042-293599-023')
DEFAULT['charlotte'] = Person(name='charlotte', home=[-39.45433139538307, 173.85871214894655], account='1042-228621-023')
DEFAULT['emily'] = Person(name='emily', home=[-39.09622892500419, 173.98472139491383], account='1042-228620-023')
DEFAULT['nigel'] = Person(name='nigel', home=[-39.04217125568929, 174.10733441465436], account='1042-228445-023')
DEFAULT['horace'] = Person(name='horace', home=[-37.81215648305214, 174.85201500441318], account='1042-228221-023')
DEFAULT['lilith'] = Person(name='lilith', home=[-37.80206926676188, 174.8872712175227], account='1042-220049-023')
DEFAULT['alistair'] = Person(name='alistair', home=[-39.84233506042953, 176.97214204174432], account='1042-299699-023')

f = ar.File('person', ar.MapOf(ar.Unicode, Person))
try:
    db = f.recover()
except ar.FileNotFound:
    db = DEFAULT
    f.store(db)

def db_query(self, who):
    return 42

def internet_request(self, coords):
    return 43

def factor_2_check(self, who):
    return 44

ar.bind(db_query)
ar.bind(internet_request)
ar.bind(factor_2_check)

#
#
class TestDbInternetDevice(TestCase):
    @classmethod
    def setUpClass(self):
        # Minimal runtime.
        p = ar.Point()
        root = p.create(ar.Channel)
        self.root = root
        pt.log_address = self.root.create(ar.LogAgent, log_to_line)
        pt.timer_address = self.root.create(tm.CountdownTimer)
        self.ticker = root.create(tm.timer_circuit, pt.timer_address)
        self.queue = self.root.create(ar.object_dispatch)
        ar.set_queue(None, self.queue)

    @classmethod
    def tearDownClass(self):
        # Take it down.
        root = self.root
        tm.circuit_ticking = False
        root.select(ar.Completed)
        root.stop(pt.timer_address)
        root.ask(ar.Enquiry(), ar.Ack, pt.log_address)
        root.stop(self.queue)
        ar.sync_complete(root)

    def setUp(self):
        global CONSOLE
        CONSOLE = []

    def tearDown(self):
        pass

    def test_db(self):
        root = self.root
        a = root.create(db_query, 'lilith')
        m = root.select(ar.Completed, seconds=0)
        assert root.return_address == a
        assert isinstance(m, ar.Completed)
        assert isinstance(m.value, int)

        root.ask(ar.Enquiry(), ar.Ack, pt.log_address)
        rv = address_log(a, True)
        assert created_destroyed(rv)

    def test_internet(self):
        root = self.root
        a = root.create(internet_request, [0.0, 0.1])
        m = root.select(ar.Completed, seconds=0)
        assert root.return_address == a
        assert isinstance(m, ar.Completed)
        assert isinstance(m.value, int)

        root.ask(ar.Enquiry(), ar.Ack, pt.log_address)
        rv = address_log(a, True)
        assert created_destroyed(rv)

    def test_device(self):
        root = self.root
        a = root.create(factor_2_check, [0.0, 0.1])
        m = root.select(ar.Completed, seconds=0)
        assert root.return_address == a
        assert isinstance(m, ar.Completed)
        assert isinstance(m.value, int)

        root.ask(ar.Enquiry(), ar.Ack, pt.log_address)
        rv = address_log(a, True)
        assert created_destroyed(rv)

