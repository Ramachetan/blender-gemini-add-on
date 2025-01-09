import bpy
import requests
import json
from bpy.props import StringProperty, PointerProperty, CollectionProperty, IntProperty, BoolProperty, FloatProperty
from bpy.types import Operator, Panel, PropertyGroup
from datetime import datetime

# Configuration
CONFIG = {
    "API_KEY": "YOUR_API_KEY_HERE",  # Replace with your Gemini API key
    "API_URL": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
    "TEMPERATURE": 0.7,
    "TOP_K": 40,
    "TOP_P": 0.95,
    "MAX_TOKENS": 8192,
    "SYSTEM_PROMPT": "You are now a specialized Python code generator for Blender 4.3. Your sole purpose is to receive requests for actions within Blender and provide the corresponding Python script."
}

bl_info = {
    "name": "Gemini Chat Assistant",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Gemini Tab",
    "description": "Chat with Gemini for Blender Python code generation",
    "category": "Development",
}

class ChatMessage(PropertyGroup):
    content: StringProperty(name="Message Content")
    role: StringProperty(name="Role")
    timestamp: StringProperty(name="Timestamp")
    is_code: BoolProperty(name="Is Code", default=False)
    is_expanded: BoolProperty(name="Is Expanded", default=True)

class GeminiProperties(PropertyGroup):
    question: StringProperty(
        name="",
        description="Enter your request here",
        default=""
    )
    api_key: StringProperty(
        name="API Key",
        description="Enter your Gemini API key",
        default="",
        subtype='PASSWORD'
    )
    chat_history: CollectionProperty(type=ChatMessage)
    chat_index: IntProperty(default=0)
    show_tips: BoolProperty(name="Show Tips", default=True)
    ui_scale: FloatProperty(name="UI Scale", default=1.0, min=0.5, max=2.0)
    auto_execute: BoolProperty(
        name="Auto-Execute Code",
        description="Automatically execute generated Python code",
        default=True
    )

class GEMINI_OT_ToggleMessage(Operator):
    bl_idname = "gemini.toggle_message"
    bl_label = "Toggle Message"
    
    index: IntProperty()
    
    def execute(self, context):
        msg = context.scene.gemini_props.chat_history[self.index]
        msg.is_expanded = not msg.is_expanded
        return {'FINISHED'}

class GEMINI_OT_CopyCode(Operator):
    bl_idname = "gemini.copy_code"
    bl_label = "Copy Code"
    
    code: StringProperty()
    
    def execute(self, context):
        context.window_manager.clipboard = self.code
        self.report({'INFO'}, "Code copied to clipboard")
        return {'FINISHED'}

class GEMINI_OT_ExecuteCode(Operator):
    bl_idname = "gemini.execute_code"
    bl_label = "Execute Code"
    
    code: StringProperty()
    
    def execute(self, context):
        try:
            exec(self.code)
            self.report({'INFO'}, "Code executed successfully")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error executing code: {str(e)}")
            return {'CANCELLED'}

class GEMINI_OT_ClearHistory(Operator):
    bl_idname = "gemini.clear_history"
    bl_label = "Clear Chat History"
    
    def execute(self, context):
        context.scene.gemini_props.chat_history.clear()
        self.report({'INFO'}, "Chat history cleared")
        return {'FINISHED'}

class GEMINI_OT_AskQuestion(Operator):
    bl_idname = "gemini.ask_question"
    bl_label = "Send Message"
    bl_description = "Send message to Gemini and execute any code response"
    
    def execute(self, context):
        props = context.scene.gemini_props
        question = props.question
        
        if not question.strip():
            self.report({'ERROR'}, "Please enter a message first")
            return {'CANCELLED'}
        
        if not props.api_key:
            self.report({'ERROR'}, "Please enter your API key in the add-on preferences")
            return {'CANCELLED'}
            
        api_url = f"{CONFIG['API_URL']}?key={props.api_key}"
        
        # Add user message to history with timestamp
        timestamp = datetime.now().strftime("%H:%M")
        
        user_msg = props.chat_history.add()
        user_msg.content = question
        user_msg.role = 'user'
        user_msg.timestamp = timestamp
        
        # Prepare chat history for API
        contents = [
            {
                "role": "user",
                "parts": [{"text": CONFIG['SYSTEM_PROMPT']}]
            }
        ]
        
        for msg in props.chat_history:
            contents.append({
                "role": msg.role,
                "parts": [{"text": msg.content}]
            })
            
        data = {
            "contents": contents,
            "generationConfig": {
                "temperature": CONFIG['TEMPERATURE'],
                "topK": CONFIG['TOP_K'],
                "topP": CONFIG['TOP_P'],
                "maxOutputTokens": CONFIG['MAX_TOKENS'],
                "responseMimeType": "text/plain"
            }
        }
        
        try:
            response = requests.post(api_url, headers={"Content-Type": "application/json"}, json=data)
            response.raise_for_status()
            
            response_data = response.json()
            response_text = response_data['candidates'][0]['content']['parts'][0]['text']
            
            # Add model response to history
            model_msg = props.chat_history.add()
            model_msg.content = response_text
            model_msg.role = 'model'
            model_msg.timestamp = timestamp
            
            # Check if response contains code
            if '```python' in response_text:
                code = response_text.split('```python')[1].split('```')[0].strip()
                model_msg.is_code = True
                
                # Store the code in a text file
                text = bpy.data.texts.new(name=f"Gemini Code {props.chat_index}")
                text.write(code)
                props.chat_index += 1
                
                # Execute the code if auto-execute is enabled
                if props.auto_execute:
                    print("Executing code:", code)
                    exec(code)
                    self.report({'INFO'}, "Code executed and saved to Text Editor")
            else:
                self.report({'INFO'}, "Received response (no code to execute)")
                
            # Clear the question field for next input
            props.question = ""
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}

class GEMINI_PT_Panel(Panel):
    bl_label = "Gemini Chat Assistant"
    bl_idname = "GEMINI_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gemini'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.gemini_props
        
        # API Key input
        api_box = layout.box()
        api_box.prop(props, "api_key", text="API Key")
        
        # Settings
        settings_box = layout.box()
        row = settings_box.row(align=True)
        row.prop(props, "auto_execute", text="Auto-Execute", icon='SCRIPT')
        row.prop(props, "show_tips", text="", icon='QUESTION')
        
        # Chat history display
        self.draw_chat_history(context, layout)
        
        # Message input area
        input_box = layout.box()
        input_box.prop(props, "question", text="")
        input_box.operator(GEMINI_OT_AskQuestion.bl_idname, icon='FORWARD')
        
        # Clear history button
        row = layout.row()
        row.operator(GEMINI_OT_ClearHistory.bl_idname, icon='TRASH')
        
        # Tips section
        if props.show_tips:
            self.draw_tips(layout)

    def draw_chat_history(self, context, layout):
        props = context.scene.gemini_props
        history_box = layout.box()
        
        if len(props.chat_history) == 0:
            history_box.label(text="No messages yet", icon='NONE')
            return
            
        for i, msg in enumerate(props.chat_history):
            message_box = history_box.box()
            
            # Header row
            header_row = message_box.row()
            header_row.label(
                text="You" if msg.role == 'user' else "Gemini",
                icon='USER' if msg.role == 'user' else 'EXPERIMENTAL'
            )
            header_row.label(text=msg.timestamp)
            
            # Toggle expand/collapse
            header_row.operator(
                GEMINI_OT_ToggleMessage.bl_idname,
                text="",
                icon='DISCLOSURE_TRI_DOWN' if msg.is_expanded else 'DISCLOSURE_TRI_RIGHT'
            ).index = i
            
            if msg.is_expanded:
                self.draw_message_content(message_box, msg)

    def draw_message_content(self, message_box, msg):
        if msg.is_code:
            code_box = message_box.box()
            code_box.alert = True
            code = msg.content.split('```python')[1].split('```')[0].strip()
            code_box.label(text="Python Code:")
            for line in code.split('\n'):
                code_box.label(text=line)
            
            # Code action buttons
            button_row = message_box.row(align=True)
            copy_op = button_row.operator(GEMINI_OT_CopyCode.bl_idname, text="Copy", icon='COPYDOWN')
            copy_op.code = code
            exec_op = button_row.operator(GEMINI_OT_ExecuteCode.bl_idname, text="Execute", icon='SCRIPT')
            exec_op.code = code
        else:
            self.draw_wrapped_text(message_box, msg.content)

    def draw_wrapped_text(self, box, text, chars_per_line=40):
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > chars_per_line:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += len(word) + 1
                
        if current_line:
            lines.append(" ".join(current_line))
            
        for line in lines:
            box.label(text=line)

    def draw_tips(self, layout):
        tips_box = layout.box()
        tips_box.label(text="Tips:", icon='INFO')
        tips_box.label(text="• Ask for 3D models or scenes")
        tips_box.label(text="• Modify previous creations")
        tips_box.label(text="• Ask about Blender features")
        tips_box.label(text="• Use 'Auto-Execute' to run code automatically")

classes = (
    ChatMessage,
    GeminiProperties,
    GEMINI_OT_ToggleMessage,
    GEMINI_OT_CopyCode,
    GEMINI_OT_ExecuteCode,
    GEMINI_OT_AskQuestion,
    GEMINI_OT_ClearHistory,
    GEMINI_PT_Panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gemini_props = PointerProperty(type=GeminiProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.gemini_props

if __name__ == "__main__":
    register()