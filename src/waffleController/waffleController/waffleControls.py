#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import evdev
from evdev import InputDevice, categorize, ecodes
import asyncio
import threading

class WaffleController(Node):
    def __init__(self):
        super().__init__('waffle_controller')
        
        # Create publisher for robot velocity commands
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        
        # Controller settings
        self.linear_speed = 0.5  # Maximum linear speed in m/s
        self.angular_speed = 1.0  # Maximum angular speed in rad/s
        
        # Initialize velocities
        self.linear_x = 0.0
        self.angular_z = 0.0
        
        # Button states
        self.button_states = {
            'U': False,  # Up
            'D': False,  # Down
            'L': False,  # Left
            'R': False,  # Right
            '1': False,  # Button 1
            '2': False,  # Button 2
            '3': False,  # Button 3
            '4': False,  # Button 4
        }
        
        # Create timer for publishing commands
        self.timer = self.create_timer(0.1, self.timer_callback)
        
        # Start controller input thread
        self.controller_thread = threading.Thread(target=self.run_controller)
        self.controller_thread.daemon = True
        self.controller_thread.start()
        
        self.get_logger().info('Waffle Controller Node Started')

    def find_controller(self):
        """Find the first available game controller."""
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            # Log available devices to help with debugging
            self.get_logger().info(f'Found device: {device.name}')
            if "controller" in device.name.lower() or "gamepad" in device.name.lower():
                return device.path
        return None

    def update_velocities(self):
        """Update velocities based on button states."""
        # Linear velocity (U/D buttons)
        if self.button_states['U'] and not self.button_states['D']:
            self.linear_x = self.linear_speed
        elif self.button_states['D'] and not self.button_states['U']:
            self.linear_x = -self.linear_speed
        else:
            self.linear_x = 0.0

        # Angular velocity (L/R buttons)
        if self.button_states['L'] and not self.button_states['R']:
            self.angular_z = self.angular_speed
        elif self.button_states['R'] and not self.button_states['L']:
            self.angular_z = -self.angular_speed
        else:
            self.angular_z = 0.0

        # Additional controls using right pad (1,2,3,4 buttons)
        # Button 1 (top) - increase linear speed
        if self.button_states['1']:
            self.linear_speed = min(1.0, self.linear_speed + 0.1)
            self.get_logger().info(f'Linear speed increased to: {self.linear_speed}')
        
        # Button 3 (bottom) - decrease linear speed
        if self.button_states['3']:
            self.linear_speed = max(0.1, self.linear_speed - 0.1)
            self.get_logger().info(f'Linear speed decreased to: {self.linear_speed}')
        
        # Button 4 (right) - increase angular speed
        if self.button_states['4']:
            self.angular_speed = min(2.0, self.angular_speed + 0.2)
            self.get_logger().info(f'Angular speed increased to: {self.angular_speed}')
        
        # Button 2 (left) - decrease angular speed
        if self.button_states['2']:
            self.angular_speed = max(0.2, self.angular_speed - 0.2)
            self.get_logger().info(f'Angular speed decreased to: {self.angular_speed}')

    def run_controller(self):
        """Handle controller input in a separate thread."""
        async def handle_events(device):
            async for event in device.async_read_loop():
                if event.type == ecodes.EV_KEY:
                    # Map button codes to our button names
                    button_map = {
                        ecodes.KEY_UP: 'U',
                        ecodes.KEY_RIGHT: 'R',
                        ecodes.KEY_DOWN: 'D',
                        ecodes.KEY_LEFT: 'L',
                        ecodes.KEY_1: '1',
                        ecodes.KEY_2: '2',
                        ecodes.KEY_3: '3',
                        ecodes.KEY_4: '4',
                    }
                    
                    if event.code in button_map:
                        button_name = button_map[event.code]
                        self.button_states[button_name] = bool(event.value)
                        self.update_velocities()
                        self.get_logger().debug(f'Button {button_name}: {self.button_states[button_name]}')

        while True:
            try:
                controller_path = self.find_controller()
                if controller_path:
                    device = InputDevice(controller_path)
                    self.get_logger().info(f'Connected to controller: {device.name}')
                    # Print device capabilities for debugging
                    self.get_logger().info(f'Device capabilities: {device.capabilities(verbose=True)}')
                    asyncio.run(handle_events(device))
                else:
                    self.get_logger().warning('No controller found. Retrying in 5 seconds...')
                    rclpy.sleep(5.0)
            except Exception as e:
                self.get_logger().error(f'Controller error: {str(e)}')
                rclpy.sleep(1.0)

    def timer_callback(self):
        """Publish velocity commands at regular intervals."""
        msg = Twist()
        msg.linear.x = self.linear_x
        msg.angular.z = self.angular_z
        self.cmd_vel_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    controller = WaffleController()
    
    try:
        rclpy.spin(controller)
    except KeyboardInterrupt:
        pass
    finally:
        controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
