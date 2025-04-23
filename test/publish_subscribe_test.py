# publish_subscribe_test.py
import uuid
from unittest import TestCase

import layer_cake as lc
import test_directory

__all__ = [
	'TestPublishSubscribe',
]

class TestPublishSubscribe(TestCase):
	def setUp(self):
		# Use explicit teardown, i.e. disable the atexit mechanism.
		# Create a channel for every test.
		# Start a host directory and give it a chance to setup listen.
		lc.PB.tear_down_atexit = False
		self.ch = lc.open_channel()
		self.directory = self.ch.create(lc.ProcessObject, test_directory.directory, directory_scope=lc.ScopeOfDirectory.HOST, accept_directories_at=lc.DIRECTORY_AT_HOST)
		self.ch.start(lc.T1, 1.0)
		self.ch.select()
		super().__init__()

	def tearDown(self):
		lc.PB.exit_status = None
		self.ch.send(lc.Stop(), self.directory)
		self.ch.select()
		lc.drop_channel(self.ch)
		lc.tear_down()
		return super().tearDown()

	def test_publish(self):
		with lc.channel() as ch:
			lc.publish(ch, 'abc')
			selected, i = ch.select()
		assert isinstance(selected, lc.Published)

	def test_listen_duplicate(self):
		with lc.channel() as ch:
			lc.publish(ch, 'abc')
			selected, i = ch.select()
			assert isinstance(selected, lc.Published)
			lc.publish(ch, 'abc')
			selected, i = ch.select()
			assert isinstance(selected, lc.NotPublished)
		e = str(selected)
		assert 'already published' in e

	def test_subscribe(self):
		with lc.channel() as ch:
			lc.subscribe(ch, 'abc')
			selected, i = ch.select()
		assert isinstance(selected, lc.Subscribed)

	def test_not_subscribed(self):
		with lc.channel() as ch:
			lc.subscribe(ch, 'abc')
			selected, i = ch.select()
			assert isinstance(selected, lc.Subscribed)
			lc.subscribe(ch, 'abc')
			selected, i = ch.select()
			assert isinstance(selected, lc.NotSubscribed)
		e = str(selected)
		assert 'already subscribed' in e

	def test_publish_and_stop(self):
		with lc.channel() as ch:
			lc.publish(ch, 'abc')
			selected, i = ch.select()
			assert isinstance(selected, lc.Published)
			lc.clear_published(ch, selected)
			selected, i = ch.select()
			assert isinstance(selected, lc.PublishedCleared)

	def test_subscribe_and_stop(self):
		with lc.channel() as ch:
			lc.subscribe(ch, 'abc')
			selected, i = ch.select()
			assert isinstance(selected, lc.Subscribed)
			lc.clear_subscribed(ch, selected)
			selected, i = ch.select()
			assert isinstance(selected, lc.SubscribedCleared)

	def test_pubsub_send_and_reply(self):
		with lc.channel() as ch:
			lc.publish(self.ch, 'abc')
			published, i = self.ch.select()
			assert isinstance(published, lc.Published)

			lc.subscribe(ch, 'abc')
			subscribed, i = ch.select()
			assert isinstance(subscribed, lc.Subscribed)

			available, i = ch.select()
			assert isinstance(available, lc.Available)

			delivered, i = self.ch.select()
			assert isinstance(delivered, lc.Delivered)

			ch.send(lc.Enquiry(), available.publisher_address)

			enquiry, i = self.ch.select()
			assert isinstance(enquiry, lc.Enquiry)

			self.ch.reply(lc.Ack())

			ack, i = ch.select()
			assert isinstance(ack, lc.Ack)

'''
	def test_listen_and_multi_connect(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected1, i = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected2, i = ch.select()
			selected3, i = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected4, i = ch.select()
			selected5, i = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected6, i = ch.select()
			selected7, i = ch.select()
		assert isinstance(selected2, (Accepted, Connected))
		assert isinstance(selected3, (Accepted, Connected))
		assert isinstance(selected4, (Accepted, Connected))
		assert isinstance(selected5, (Accepted, Connected))
		assert isinstance(selected6, (Accepted, Connected))
		assert isinstance(selected7, (Accepted, Connected))

	def test_no_connect(self):
		with lc.channel() as ch:
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5051))
			selected, i = ch.select()
		assert isinstance(selected, NotConnected)
		e = str(selected)
		assert 'refused' in e

	def test_send(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected1, i = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected2, i = ch.select()
			if isinstance(selected2, Connected):
				server = ch.return_address
			selected3, i = ch.select()
			if isinstance(selected3, Connected):
				server = ch.return_address
			ch.send(lc.cast_to(42, lc.int_type), server)
			selected, i = ch.select()
			ch.send(lc.cast_to([[0.125, 30.02],[0.5, 2.5],[1.1, 2.2, 3.3]], table_type), server)
			selected, i = ch.select()
			ch.send(lc.Ack(), server)
			selected, i = ch.select()
		assert isinstance(selected, lc.Ack)

table_type = lc.def_type(list[list[float]])
'''