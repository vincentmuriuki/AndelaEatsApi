from tests.base_test_case import BaseTestCase
from factories import OrderFactory, MealItemFactory, RoleFactory, PermissionFactory, UserRoleFactory, MenuFactory, LocationFactory
from app.utils.enums import MealTypes
from json import loads
from datetime import date, timedelta
from app.utils import db
from app.repositories import OrderRepo
from app.utils.enums import OrderStatus


class TestOrderEndpoints(BaseTestCase):

	def setUp(self):
		self.BaseSetUp()

	def test_create_order_with_invalid_details_endpoint(self):
		items = [item.id for item in MealItemFactory.create_batch(4)]
		menu = MenuFactory.create()
		
		LocationFactory.create(id=1, zone='+1')
		data = {'dateBookedFor': (date.today() + timedelta(days=-3)).strftime('%Y-%m-%d'), 'channel': 'web', 'mealPeriod': 'lunch', 'menuId': menu.id}

		# If we don't add meal items
		response = self.client().post(self.make_url('/orders/'), data=self.encode_to_json_string(data), headers=self.headers())
		self.assert400(response)

		# If we book in the past
		data.update({'mealItems': items})
		response1 = self.client().post(self.make_url('/orders/'), data=self.encode_to_json_string(data), headers=self.headers())
		self.assert400(response1)
		
		data.update({'dateBookedFor': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')})
		
		response2 = self.client().post(self.make_url('/orders/'), data=self.encode_to_json_string(data), headers=self.headers())
		self.assertEqual(response2.status_code, 201)

	def test_create_order_with_valid_details_endpoint(self):
		LocationFactory.create(id=1, zone='+1')
		order = OrderFactory.create()
		menu = MenuFactory.create()
		meal_item1 = MealItemFactory.create()
		meal_item2 = MealItemFactory.create()
		meal_item3 = MealItemFactory.create()
		meal_item1.meal_type = MealTypes.protein
		meal_item2.meal_type = MealTypes.main

		meal_items = [meal_item1.id, meal_item2.id, meal_item3.id]
		data = {'userId': order.user_id, 'dateBookedFor': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
				'dateBooked': order.date_booked.strftime('%Y-%m-%d'), 'channel': 'web', 'menuId': menu.id,
				'mealPeriod': order.meal_period, 'mealItems': meal_items}

		response = self.client().post(
			self.make_url('/orders/'), data=self.encode_to_json_string(data), headers=self.headers())

		response_json = self.decode_from_json_string(response.data.decode('utf-8'))
		
		payload = response_json['payload']
		self.assertEqual(response.status_code, 201)
		self.assertJSONKeyPresent(response_json, 'payload')
		self.assertEqual(payload['order']['userId'], BaseTestCase.user_id())
		self.assertEqual(payload['order']['channel'], 'web')

	def test_list_order_endpoint(self):
		# Create Three Dummy Vendors
		OrderFactory.create_batch(3)
		role = RoleFactory.create(name='admin')
		user_id = BaseTestCase.user_id()
		PermissionFactory.create(keyword='view_orders', role_id=role.id)
		UserRoleFactory.create(user_id=user_id, role_id=role.id)

		response = self.client().get(self.make_url('/orders/'), headers=self.headers())
		response_json = self.decode_from_json_string(response.data.decode('utf-8'))
		payload = response_json['payload']
		self.assert200(response)
		self.assertEqual(len(payload['orders']), 3)
		self.assertJSONKeysPresent(payload['orders'][0], 'userId', 'channel', 'dateBookedFor')

	def test_list_order_by_page_endpoint(self):
		OrderFactory.create_batch(3)
		role = RoleFactory.create(name='admin')
		user_id = BaseTestCase.user_id()
		PermissionFactory.create(keyword='view_orders', role_id=role.id)
		UserRoleFactory.create(user_id=user_id, role_id=role.id)

		response = self.client().get(self.make_url('/orders/'), query_string={'per_page': 2, 'page': 1}, headers=self.headers())
		decoded = loads(response.data, encoding='utf-8')
		self.assert200(response)
		self.assertEqual(decoded['payload']['meta']['current_page'], 1)
		self.assertEqual(len(decoded['payload']['orders']), 2)

		response1 = self.client().get(self.make_url('/orders/'), query_string={'per_page': 2, 'page': 2}, headers=self.headers())
		self.assert200(response1)
		decoded1 = loads(response1.data, encoding='utf-8')
		self.assertEqual(decoded1['payload']['meta']['current_page'], 2)
		self.assertEqual(len(decoded1['payload']['orders']), 1)

	def test_list_order_by_date_endpoint(self):
		OrderFactory.create_batch(3)
		book_date = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
		role = RoleFactory.create(name='admin')
		user_id = BaseTestCase.user_id()
		PermissionFactory.create(keyword='view_orders', role_id=role.id)
		UserRoleFactory.create(user_id=user_id, role_id=role.id)

		response = self.client().get(self.make_url('/orders/2008-11-20'), headers=self.headers())
		self.assert200(response)
		self.assertEqual(len(loads(response.data, encoding='utf-8')['payload']['orders']), 0)

		response1 = self.client().get(self.make_url('/orders/{}'.format(book_date)), headers=self.headers())
		self.assert200(response1)
		self.assertEqual(len(loads(response1.data, encoding='utf-8')['payload']['orders']), 3)

	def test_check_order_valid_endpoint(self):
		order = OrderFactory.create()
		role = RoleFactory.create(name='admin')
		user_id = BaseTestCase.user_id()
		order.meal_period, order.user_id = 'lunch', user_id
		PermissionFactory.create(keyword='view_orders', role_id=role.id)
		UserRoleFactory.create(user_id=user_id, role_id=role.id)

		data={'userId': user_id, 'orderType': order.meal_period, 'orderDate': order.date_booked_for.strftime('%Y-%m-%d')}
		response = self.client().post(self.make_url('/orders/check'), data=self.encode_to_json_string(data) , headers=self.headers())
		self.assert200(response)

	def test_check_order_valid_but_cancelled_endpoint(self):
		order = OrderFactory.create()
		role = RoleFactory.create(name='admin')
		user_id = BaseTestCase.user_id()
		order.meal_period, order.user_id = 'lunch', user_id
		order.order_status = OrderStatus.cancelled
		PermissionFactory.create(keyword='view_orders', role_id=role.id)
		UserRoleFactory.create(user_id=user_id, role_id=role.id)

		data = {'userId': user_id, 'orderType': order.meal_period, 'orderDate': order.date_booked_for.strftime('%Y-%m-%d')}
		response = self.client().post(self.make_url('/orders/check'), data=self.encode_to_json_string(data) , headers=self.headers())
		self.assert200(response)
		self.assertEqual(loads(response.data, encoding='utf-8')['payload']['order']['orderStatus'], 'cancelled')

	def test_check_order_valid_but_collected_endpoint(self):
		order = OrderFactory.create()
		role = RoleFactory.create(name='admin')
		user_id = BaseTestCase.user_id()
		order.meal_period, order.user_id = 'lunch', user_id
		order.order_status = OrderStatus.collected
		PermissionFactory.create(keyword='view_orders', role_id=role.id)
		UserRoleFactory.create(user_id=user_id, role_id=role.id)

		data = {'userId': user_id, 'orderType': order.meal_period, 'orderDate': order.date_booked_for.strftime('%Y-%m-%d')}
		response = self.client().post(self.make_url('/orders/check'), data=self.encode_to_json_string(data) , headers=self.headers())
		self.assert200(response)
		self.assertEqual(loads(response.data, encoding='utf-8')['payload']['order']['orderStatus'], 'collected')

	def test_check_order_not_valid_endpoint(self):
		order = OrderFactory.create()
		role = RoleFactory.create(name='admin')
		user_id = BaseTestCase.user_id()
		order.meal_period, order.user_id = 'lunch', user_id
		PermissionFactory.create(keyword='view_orders', role_id=role.id)
		UserRoleFactory.create(user_id=user_id, role_id=role.id)

		data={'user_id': user_id, 'order_type': 'blahblah', 'order_date': order.date_booked_for.strftime('%Y-%m-%d')}
		response = self.client().post(self.make_url('/orders/check'), data=self.encode_to_json_string(data) , headers=self.headers())
		self.assert400(response)

	def test_collect_order_valid_endpoint(self):
		order = OrderFactory.create()
		role = RoleFactory.create(name='admin')
		user_id = BaseTestCase.user_id()
		order.meal_period, order.user_id = 'lunch', user_id
		PermissionFactory.create(keyword='view_orders', role_id=role.id)
		UserRoleFactory.create(user_id=user_id, role_id=role.id)

		data = {'userId': user_id, 'orderType': order.meal_period, 'orderDate': order.date_booked_for.strftime('%Y-%m-%d')}
		response = self.client().post(self.make_url('/orders/collect'), data=self.encode_to_json_string(data) , headers=self.headers())
		self.assert200(response)

	def test_collect_order_already_collected(self):
		order = OrderFactory.create()
		role = RoleFactory.create(name='admin')
		user_id = BaseTestCase.user_id()
		order.meal_period, order.user_id = 'lunch', user_id
		PermissionFactory.create(keyword='view_orders', role_id=role.id)
		UserRoleFactory.create(user_id=user_id, role_id=role.id)

		data = {'userId': user_id, 'orderType': order.meal_period, 'orderDate': order.date_booked_for.strftime('%Y-%m-%d')}
		response = self.client().post(self.make_url('/orders/collect'), data=self.encode_to_json_string(data) , headers=self.headers())
		self.assert200(response)

		response1 = self.client().post(self.make_url('/orders/collect'), data=self.encode_to_json_string(data) , headers=self.headers())
		self.assertEqual(response1.status_code, 200)

	def test_collect_order_not_valid_endpoint(self):
		order = OrderFactory.create()
		role = RoleFactory.create(name='admin')
		user_id = BaseTestCase.user_id()
		order.meal_period, order.user_id = 'lunch', user_id
		PermissionFactory.create(keyword='view_orders', role_id=role.id)
		UserRoleFactory.create(user_id=user_id, role_id=role.id)

		data={'userId': user_id, 'orderType': 'blahblah', 'orderDate': order.date_booked_for.strftime('%Y-%m-%d')}
		response = self.client().post(self.make_url('/orders/collect'), data=self.encode_to_json_string(data) , headers=self.headers())
		self.assert200(response)

	def test_get_all_orders_by_user_id_endpoint(self):
		orders = OrderFactory.create_batch(3)
		role = RoleFactory.create(name='admin')
		user_id = BaseTestCase.user_id()
		for order in orders:
			order.user_id = user_id
		PermissionFactory.create(keyword='view_orders', role_id=role.id)
		UserRoleFactory.create(user_id=user_id, role_id=role.id)

		response = self.client().get(self.make_url('/orders/user/{}'.format(user_id)), headers=self.headers())
		self.assert200(response)
		self.assertEqual(len(loads(response.data, encoding='utf-8')['payload']['orders']), 3)

	def test_get_specific_meal_item_endpoint(self):
		order = OrderFactory.create()
		print('/orders/{}/'.format(order.id))

		response = self.client().get(self.make_url('/orders/{}'.format(order.id)), headers=self.headers())
		response_json = self.decode_from_json_string(response.data.decode('utf-8'))
		payload = response_json['payload']

		self.assert200(response)
		self.assertJSONKeyPresent(payload, 'order')
		self.assertJSONKeysPresent(payload['order'], 'userId', 'channel')
		self.assertEqual(int(payload['order']['id']), order.id)
		self.assertEqual(payload['order']['userId'], order.user_id)
		self.assertEqual(payload['order']['channel'], order.channel)

	def test_update_order_with_valid_order_id_endpoint(self):
		order1 = OrderFactory.create()
		order2 = OrderFactory.create()

		meal_item1 = MealItemFactory.create()
		meal_item2 = MealItemFactory.create()
		meal_item3 = MealItemFactory.create()
		meal_item1.meal_type = MealTypes.protein
		meal_item2.meal_type = MealTypes.main

		meal_items = [meal_item1.id, meal_item2.id, meal_item3.id]

		data = {
			'channel': 'slack', 'mealPeriod': 'lunch',
			'dateBookedFor': order2.date_booked_for.strftime('%Y-%m-%d'), 'mealItems': meal_items}
		response = self.client().put(
			self.make_url('/orders/{}'.format(order1.id)), data=self.encode_to_json_string(data), headers=self.headers())
		response_json = self.decode_from_json_string(response.data.decode('utf-8'))
		payload = response_json['payload']

		self.assert200(response)
		self.assertEqual(payload['order']['channel'], data['channel'])

		'''Test invalid update request'''
		# User arbitrary value of 100 as the meal item ID
		response = self.client().put(
			self.make_url('/orders/100'), data=self.encode_to_json_string(data), headers=self.headers())
		self.assert400(response)

	def test_update_order_with_invalid_order_id_endpoint(self):
		pass

	def test_delete_order_endpoint_with_right_permission(self):
		user_id = BaseTestCase.user_id()
		meal = MealItemFactory.create()
		menu = MenuFactory.create()
		order_data = {
			'user_id': user_id,
			'date_booked_for': '2018-10-20',
			'channel': 'web', 'meal_period': 'lunch', 'menu_id': menu.id,
			'meal_items': [meal], 'location_id': 1
		}
		order_repo = OrderRepo()
		order = order_repo.create_order(**order_data)

		response = self.client().delete(self.make_url(f'/orders/{order.id}'), headers=self.headers())
		response_json = self.decode_from_json_string(response.data.decode('utf-8'))
		payload = response_json['payload']

		self.assert200(response)
		self.assertEqual(payload['status'], 'success')
		self.assertEqual(response_json['msg'], 'Order deleted')

	def test_delete_order_not_yours(self):
		user_id = BaseTestCase.user_id()
		meal = MealItemFactory.create()
		menu = MenuFactory.create()
		order_data = {
			'user_id': '-UTG654RfggtdI',
			'date_booked_for': '2018-10-20',
			'channel': 'web', 'meal_period': 'lunch', 'menu_id': menu.id,
			'meal_items': [meal], 'location_id': 1
		}
		order_repo = OrderRepo()
		order = order_repo.create_order(**order_data)

		response = self.client().delete(self.make_url(f'/orders/{order.id}'), headers=self.headers())
		response_json = self.decode_from_json_string(response.data.decode('utf-8'))

		self.assert403(response)
		self.assertEqual(response_json['msg'], 'You cannot delete an order that is not yours')

	def test_delete_order_endpoint_with_wrong_order_id(self):
		response = self.client().delete(self.make_url(f'/orders/576'), headers=self.headers())
		response_json = self.decode_from_json_string(response.data.decode('utf-8'))

		self.assert400(response)
		self.assertEqual(response_json['msg'], 'Invalid or incorrect order_id provided')

	def test_already_deleted_order(self):
		user_id = BaseTestCase.user_id()
		meal = MealItemFactory.create()
		menu = MenuFactory.create()
		order_data = {
			'user_id': user_id,
			'date_booked_for': '2018-10-20',
			'channel': 'web', 'meal_period': 'lunch', 'menu_id': menu.id,
			'meal_items': [meal], 'location_id': 1
		}
		order_repo = OrderRepo()
		order = order_repo.create_order(**order_data)

		self.client().delete(self.make_url(f'/orders/{order.id}'), headers=self.headers())
		response = self.client().delete(self.make_url(f'/orders/{order.id}'), headers=self.headers())
		response_json = self.decode_from_json_string(response.data.decode('utf-8'))

		self.assert400(response)
		self.assertEqual(response_json['msg'], 'Order has already been deleted')
