from flask import Blueprint, request, jsonify
from ddd.user_management.application.commands.register_user_command import (
    RegisterUserCommand,
    ChangePasswordCommand,
    DeactivateUserCommand,
    ActivateUserCommand,
    UpdateUserProfileCommand,
)
from ddd.user_management.application.queries.get_user_queries import (
    GetUserByEmailQuery,
    GetUserByIdQuery,
    VerifyUserPasswordQuery,
)
from ddd.user_management.domain.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    InvalidEmailError,
    InvalidPasswordError,
)
from ddd.user_management.application.commands.login_user_command import (
    LoginUserCommand,
)

def create_user_routes(container):
    user_bp = Blueprint('user_api', __name__, url_prefix='/users')
    

    @user_bp.route('/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('email') or not data.get('password'):
                return jsonify({'error': 'Email and password are required'}), 400
            
            # Create command
            command = RegisterUserCommand(
                email=data['email'],
                password=data['password'],
                full_name=data.get('full_name', ''),
                phone=data.get('phone'),
                role=data.get('role', 'customer'),
            )
            
            # Execute via handler
            handler = container.get('register_user_handler')
            result = handler.execute(command)
            
            return jsonify(result.to_dict()), 201
        
        except UserAlreadyExistsError as e:
            return jsonify({'error': str(e)}), 409
        except (InvalidEmailError, InvalidPasswordError) as e:
            return jsonify({'error': str(e)}), 422
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    

    @user_bp.route('/<user_id>', methods=['GET'])
    def get_user(user_id):
        try:
            query = GetUserByIdQuery(user_id=user_id)
            handler = container.get('get_user_by_id_handler')
            user_dto = handler.execute(query)
            
            if not user_dto:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify(user_dto.to_dict()), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    
    @user_bp.route('/email/<email>', methods=['GET'])
    def get_user_by_email(email):
        try:
            query = GetUserByEmailQuery(email=email)
            handler = container.get('get_user_by_email_handler')
            user_dto = handler.execute(query)
            
            if not user_dto:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify(user_dto.to_dict()), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    

    @user_bp.route('/<user_id>/change-password', methods=['POST'])
    def change_password(user_id):
        try:
            data = request.get_json()
            
            if not data.get('old_password') or not data.get('new_password'):
                return jsonify({'error': 'Old and new password are required'}), 400
            
            command = ChangePasswordCommand(
                user_id=user_id,
                old_password=data['old_password'],
                new_password=data['new_password'],
            )
            
            handler = container.get('change_password_handler')
            result = handler.execute(command)
            
            return jsonify(result.to_dict()), 200
        
        except UserNotFoundError as e:
            return jsonify({'error': str(e)}), 404
        except InvalidPasswordError as e:
            return jsonify({'error': str(e)}), 422
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    

    @user_bp.route('/<user_id>/profile', methods=['PUT'])
    def update_profile(user_id):
        try:
            data = request.get_json()
            
            command = UpdateUserProfileCommand(
                user_id=user_id,
                full_name=data.get('full_name'),
                phone=data.get('phone'),
            )
            
            handler = container.get('update_user_profile_handler')
            result = handler.execute(command)
            
            return jsonify(result.to_dict()), 200
        
        except UserNotFoundError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    

    @user_bp.route('/<user_id>/deactivate', methods=['POST'])
    def deactivate_user(user_id):
        try:
            command = DeactivateUserCommand(user_id=user_id)
            handler = container.get('deactivate_user_handler')
            result = handler.execute(command)
            
            return jsonify(result.to_dict()), 200
        
        except UserNotFoundError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @user_bp.route('/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()

            # Validate required fields
            if not data.get('email') or not data.get('password'):
                return jsonify({'error': 'Email and password are required'}), 400

            # Create command
            command = LoginUserCommand(
                email=data['email'],
                password=data['password']
            )

            # Execute via handler
            handler = container.get('login_user_handler')
            result = handler.execute(command)

            return jsonify(result.to_dict()), 200

        except UserNotFoundError as e:
            return jsonify({'error': str(e)}), 404
        except InvalidPasswordError as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return user_bp
