import uuid
import json

import requests
from requests import Response

from hstest import FlaskTest, dynamic_test, wrong, correct, SQLTest, StageTest


class ServerTest(FlaskTest):
    use_database = False
    source = 'task'
    existing_user = f"{uuid.uuid4()}@mail.ru"

    @dynamic_test
    def test_register_201(self):
        hw = requests.post(self.get_url('/users'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        try:
            json.loads(hw.content)
        except Exception:
            return wrong(f'Response should be in json format')

        if hw.status_code != 201:
            return wrong('Response code of successful POST method should be 201')

        if 'message' not in hw.json():
            return wrong('Register endpoint should return "message" field about successful user registration')

        return correct()

    # append to list ok
    @dynamic_test
    def test_post_append_201(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=headers,
        )
        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)

        if len(hw.json().get('todo_list')) != 1:
            return wrong('Wrong list length')

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    ),
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    ),
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ],
                "list_id": created_list_id
            },
            headers=headers,
        )
        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)

        if len(hw.json().get('todo_list')) != 4:
            return wrong('Wrong list length')
        return correct()

    # append to list no right at all
    @dynamic_test
    def test_post_append_401(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=headers,
        )

        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)

        if len(hw.json().get('todo_list')) != 1:
            return wrong('Wrong list length')

        # register here:
        new_email = f"{uuid.uuid4()}@mail.com"
        hw = requests.post(self.get_url('/users'), json={
            "email": new_email,
            "password": "132"
        })
        hw = requests.post(self.get_url('/login'), json={
            "email": new_email,
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ],
                "list_id": created_list_id
            },
            headers=headers,
        )
        if hw.status_code != 401:
            return wrong('not author should not have access to the list without sharing it to them')

        return correct()

    # append to list no write right:
    @dynamic_test
    def test_post_list_can_only_read_401(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        strong_headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=strong_headers,
        )

        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=strong_headers)

        if len(hw.json().get('todo_list')) != 1:
            return wrong('Wrong list length')

        # register here:
        new_email = f"{uuid.uuid4()}@mail.com"
        hw = requests.post(self.get_url('/users'), json={
            "email": new_email,
            "password": "132"
        })
        hw = requests.post(self.get_url('/login'), json={
            "email": new_email,
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw = requests.get(self.get_url(f'/users?email={new_email}'))
        hw = requests.post(self.get_url('/access'), json={
            "user_id": hw.json().get('user_id'),
            "list_id": created_list_id
        }, headers=strong_headers)

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ],
                "list_id": created_list_id
            },
            headers=headers,
        )
        if hw.status_code != 401:
            return wrong('not author should not have access to the list without sharing it to them')

        return correct()

    # share ok
    @dynamic_test
    def test_share_read_access_200(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        strong_headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=strong_headers,
        )

        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=strong_headers)

        if len(hw.json().get('todo_list')) != 1:
            return wrong('Wrong list length')

        # register here:
        new_email = f"{uuid.uuid4()}@mail.com"
        hw = requests.post(self.get_url('/users'), json={
            "email": new_email,
            "password": "132"
        })
        hw = requests.post(self.get_url('/login'), json={
            "email": new_email,
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw = requests.get(self.get_url(f'/users?email={new_email}'))
        hw = requests.post(self.get_url('/access'), json={
            "user_id": hw.json().get('user_id'),
            "list_id": created_list_id
        }, headers=strong_headers)

        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)

        if hw.status_code != 200:
            return wrong('after sharing user with access should be able to read shared list')

        return correct()

    # share no right
    def test_share_read_access_No_right_to_share_401(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        strong_headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=strong_headers,
        )

        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=strong_headers)

        if len(hw.json().get('todo_list')) != 1:
            return wrong('Wrong list length')

        # register here:
        new_email = f"{uuid.uuid4()}@mail.com"
        hw = requests.post(self.get_url('/users'), json={
            "email": new_email,
            "password": "132"
        })
        hw = requests.post(self.get_url('/login'), json={
            "email": new_email,
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw = requests.get(self.get_url(f'/users?email={new_email}'))
        hw = requests.post(self.get_url('/access'), json={
            "user_id": hw.json().get('user_id'),
            "list_id": created_list_id
        }, headers=headers)

        if hw.status_code != 401:
            return wrong('not author should not be able to share list and should get 401 code')

        return correct()

    # share no list
    @dynamic_test()
    def test_share_read_access_no_list_to_share_400(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        strong_headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=strong_headers,
        )
        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=strong_headers)
        hw = requests.get(self.get_url('/users'), params={
                "email": self.existing_user,
                })
        hw = requests.post(self.get_url('/access'), json={
            "user_id": hw.json().get('user_id'),
            "list_id": created_list_id + 1
        }, headers=strong_headers)
        if hw.status_code != 400:
            return wrong('request to share non existent list should return 400')

        return correct()

    # share no user
    @dynamic_test()
    def test_share_read_access_no_user_to_share_with_400(self):
        new_email = f'{uuid.uuid4()}@mail.com'
        hw = requests.post(self.get_url('/users'), json={
            "email": new_email,
            "password": "132"
        })
        hw = requests.post(self.get_url('/login'), json={
            "email": new_email,
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw = requests.get(self.get_url(f'/users?email={new_email}'))
        user_id = hw.json().get('user_id')

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=headers,
        )

        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url('/users'), params={
                "email": self.existing_user,
                })
        hw = requests.post(self.get_url('/access'), json={
            "user_id": user_id + 1,
            "list_id": created_list_id
        }, headers=headers)
        if hw.status_code != 400:
            return wrong('request to share with non existent user should return 400')

        return correct()

    # unshare ok
    @dynamic_test
    def test_share_read_access_200(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        strong_headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=strong_headers,
        )

        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=strong_headers)

        if len(hw.json().get('todo_list')) != 1:
            return wrong('Wrong list length')

        # register here:
        new_email = f"{uuid.uuid4()}@mail.com"
        hw = requests.post(self.get_url('/users'), json={
            "email": new_email,
            "password": "132"
        })
        hw = requests.post(self.get_url('/login'), json={
            "email": new_email,
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw = requests.get(self.get_url(f'/users?email={new_email}'))
        hw = requests.post(self.get_url('/access'), json={
            "user_id": hw.json().get('user_id'),
            "list_id": created_list_id
        }, headers=strong_headers)

        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)

        if hw.status_code != 200:
            return wrong('after sharing user with access should be able to read shared list')

        return correct()

    # unshare no right
    def test_revoke_read_access_No_right_to_share_401(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        strong_headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=strong_headers,
        )

        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=strong_headers)

        if len(hw.json().get('todo_list')) != 1:
            return wrong('Wrong list length')

        # register here:
        new_email = f"{uuid.uuid4()}@mail.com"
        hw = requests.post(self.get_url('/users'), json={
            "email": new_email,
            "password": "132"
        })
        hw = requests.post(self.get_url('/login'), json={
            "email": new_email,
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw = requests.get(self.get_url(f'/users?email={new_email}'))
        hw = requests.delete(self.get_url('/access'), json={
            "user_id": hw.json().get('user_id'),
            "list_id": created_list_id
        }, headers=headers)

        if hw.status_code != 401:
            return wrong('not author should not be able to revoke shared access list and should get 401 code')

        return correct()

    # unshare no list
    @dynamic_test()
    def test_revoke_read_access_no_list_to_share_400(self):
        hw = requests.post(self.get_url('/login'), json={
            "email": f"{self.existing_user}",
            "password": "132"
        })

        token = hw.json().get('access_token')
        strong_headers = {'Authorization': f'Bearer {token}'}

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=strong_headers,
        )
        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=strong_headers)
        hw = requests.get(self.get_url('/users'), params={
                "email": self.existing_user,
                })
        hw = requests.delete(self.get_url('/access'), json={
            "user_id": hw.json().get('user_id'),
            "list_id": created_list_id + 1
        }, headers=strong_headers)
        if hw.status_code != 400:
            return wrong('request to revoke access to non existent list should return 400')

        return correct()

    # unshare no user
    @dynamic_test()
    def test_revoke_read_access_no_user_to_share_with_400(self):
        new_email = f'{uuid.uuid4()}@mail.com'
        hw = requests.post(self.get_url('/users'), json={
            "email": new_email,
            "password": "132"
        })
        hw = requests.post(self.get_url('/login'), json={
            "email": new_email,
            "password": "132"
        })

        token = hw.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        hw = requests.get(self.get_url(f'/users?email={new_email}'))
        user_id = hw.json().get('user_id')

        hw: Response = requests.post(
            self.get_url('/lists'),
            json={
                "list": [
                    dict(
                        title='title',
                        description='descr',
                        deadline_time='2001-01-01 12:00:00',
                        is_completed=False
                    )
                ]
            },
            headers=headers,
        )

        created_list_id = hw.json().get('created_list_id')
        hw = requests.get(self.get_url('/users'), params={
                "email": self.existing_user,
                })
        hw = requests.delete(self.get_url('/access'), json={
            "user_id": user_id + 1,
            "list_id": created_list_id
        }, headers=headers)
        if hw.status_code != 400:
            return wrong('request to revoke access with non existent user should return 400')

        return correct()

    # get list ok


    # get list no right

    # @dynamic_test
    # def test_get_list_200(self):
    #     hw = requests.post(self.get_url('/login'), json={
    #         "email": f"{self.existing_user}",
    #         "password": "132"
    #     })
    #
    #     token = hw.json().get('access_token')
    #     headers = {'Authorization': f'Bearer {token}'}
    #
    #     hw: Response = requests.post(
    #         self.get_url('/lists'),
    #         json={
    #             "list": [
    #                 dict(
    #                     title='title',
    #                     description='descr',
    #                     deadline_time='2001-01-01 12:00:00',
    #                     is_completed=False
    #                 )
    #             ]
    #         },
    #         headers=headers,
    #     )
    #     created_list_id = hw.json().get('created_list_id')
    #
    #     hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)
    #
    #     if len(hw.json().get('todo_list')) != 1:
    #         return wrong('Number of created elements in list is not correct')
    #
    #     return correct()
    #
    # @dynamic_test
    # def test_get_list_401(self):
    #     hw = requests.post(self.get_url('/login'), json={
    #         "email": f"{self.existing_user}",
    #         "password": "132"
    #     })
    #
    #     token = hw.json().get('access_token')
    #     headers = {'Authorization': f'Bearer {token}'}
    #
    #     hw: Response = requests.post(
    #         self.get_url('/lists'),
    #         json={
    #             "list": [
    #                 dict(
    #                     title='title',
    #                     description='descr',
    #                     deadline_time='2001-01-01 12:00:00',
    #                     is_completed=False
    #                 )
    #             ]
    #         },
    #         headers=headers,
    #     )
    #     created_list_id = hw.json().get('created_list_id')
    #     new_user = f"{uuid.uuid4()}@mail.com"
    #     hw = requests.post(self.get_url('/users'), json={
    #         "email": new_user,
    #         "password": "132"
    #     })
    #     hw = requests.post(self.get_url('/login'), json={
    #         "email": new_user,
    #         "password": "132"
    #     })
    #     token = hw.json().get('access_token')
    #     headers = {'Authorization': f'Bearer {token}'}
    #
    #     hw = requests.get(self.get_url(f'/lists/{created_list_id}'), headers=headers)
    #     if hw.status_code != 401:
    #         return wrong('lists created by one user should no be accessible by others')
    #
    #     return correct()
    #
