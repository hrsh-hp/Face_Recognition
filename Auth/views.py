from django.http import JsonResponse,HttpResponse
from django.shortcuts import render,redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import *
from django.contrib.auth import authenticate,login,logout,get_user_model
import uuid
from .helpers import send_email_token
from django.contrib import messages
import asyncio
from django.core.cache import cache

User = get_user_model()

#for face recogniton
import face_recognition
import base64
import cv2
from PIL import Image
import numpy as np
from io import BytesIO

known_faces = {}

def get_known_face_encoding():
    known_face_encodings = []
    for face_obj in User.objects.filter(is_superuser = False):
        known_image_data = base64.b64decode(face_obj.user_image.split(',')[1])
        known_image = Image.open(BytesIO(known_image_data))
        known_face_encodings = face_recognition.face_encodings(np.array(known_image))
        # print(known_face_encodings)
        if known_face_encodings:
            known_faces[face_obj.email] = known_face_encodings[0]

    return known_faces

def update_known_faces():
    known_faces = get_known_face_encoding()
    cache.set('known_faces', known_faces, timeout=None) 
    
def index(request):
    known_faces = cache.get('known_faces')
    if known_faces is None:
        update_known_faces()
    print(request.user)
    current_user = User.objects.filter(email = request.user)
    if not current_user:
        messages.info(request, "You are not logged in Log-in first.")
        return redirect('Auth:login_page')
    return render(request, 'index.html')

                    
# Face Recognition view 
@csrf_exempt
def recognize_face(request):
    # print(known_faces)
    known_faces = cache.get('known_faces', {})
    if request.method == "POST":
        try:
            # decoding the base64 received from frontend into image
            image_data = request.POST.get('imageData')
            img_data = base64.b64decode(image_data.split(',')[1])
            # print(img_data)
            image = Image.open(BytesIO(img_data))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # getting face encodings from received image
            rec_face_locations = face_recognition.face_locations(frame, number_of_times_to_upsample=2)
            rec_face_encodings = face_recognition.face_encodings(frame,rec_face_locations)
         
            recognized_name = []
            email = "Unknown!!"
            student = {"email":email}
            
            #comparing known face encodings with received face encodings
            for rec_face_encoding in rec_face_encodings:
                matches = face_recognition.compare_faces(list(known_faces.values()), rec_face_encoding)  
                # print(known_faces.values())              
                if True in matches:
                    first_match_index = matches.index(True)
                    email = list(known_faces.keys())[first_match_index]
                    print(f"Welcome {email}")
                    recognized_name.append(email)
                    recognized_user = User.objects.filter(email = email ).first()
                    print(recognized_user.first_name)
                    student = {
                        "email":email,
                        "name":recognized_user.first_name+" "+ recognized_user.last_name,
                        "enrollment": recognized_user.enrollment,
                        "department": recognized_user.department
                    }
                    
                else :
                    print('face not matches')
                  
            print(recognized_name)
            
            # Convert a frame in to Jpeg
            _ , jpeg = cv2.imencode('.jpeg', frame)
            res_img = jpeg.tobytes()  
            response = base64.b64encode(res_img).decode('utf-8')
           
            return JsonResponse({'student':student,'image':response, "success": True})
                    
        except Exception as e:
            print(e)
            return JsonResponse({'err':str(e),"success":False})
        
    else:
        print('not a Post method')
        return JsonResponse({'err':"Invalid request method it must be POST"})
    

#Register Page logic
@csrf_exempt
def register(request):
    #When user request for registraion
    
    if request.method == "POST":
        try:
            email = request.POST.get('email')
            phone_num = request.POST.get('phone_num')
            password = request.POST.get('pasword')
            enrollment = request.POST.get('enrollment')
            first_name = request.POST.get('first_name')
            print(first_name)
            if first_name == "":
                first_name = str(email).split('@')[0] 
                print(first_name)  
            last_name = request.POST.get('last_name')
            user_image = request.POST.get('image_base64')
            # print(user_image)
            email_token = str(uuid.uuid4())
            user = User.objects.create(
                email= email,
                phone_num= phone_num,
                first_name = first_name,
                last_name = last_name,
                user_image = user_image,
                enrollment = enrollment
            )
            user.set_password(password)
            user.email_token = email_token
            user.save()
            email_sent = send_email_token(email, email_token)
            if email_sent is False:
                messages.info(request, "There's some problem in sending mail to you plese check your email.")
                return redirect('Auth:register')
            
            messages.info(request, "A verification mail is sent to your mail id")
            return redirect('Auth:register')
                
            
        except Exception as e:
            print(e)
            messages.info(request, "Something went wrong now.")
            return redirect('Auth:register')
   
    #when user send request to view template
    return render(request, 'register.html')

@csrf_exempt
def verify(request, email_token):
    try:
        user_obj = User.objects.filter(email_token = email_token).first()
    
        if user_obj:
            if user_obj.is_email_verified:
                messages.info(request, "Your email is already verified You can Log-In.")
                return redirect("Auth:login_page")
            
            user_obj.is_email_verified = True
            user_obj.save()
            messages.info(request, "Your account has been verified you can Log-In now.")
            return redirect('Auth:login_page')
            
        else:
            messages.info(request, "Invalid verification link.")
            return redirect('Auth:register')
                    
    except Exception as e:
        print(e)

@csrf_exempt
def login_page(request):
    
    if request.method == "POST":
        try:
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            user_obj = User.objects.filter(email = email).first()
            
            if user_obj is None:
                messages.info(request, "No user with this email is exist you can Register.")
                return redirect('Auth:register')
            
            if not user_obj.is_email_verified:
                messages.info(request, "Your email is not verified please verify first.")
                return redirect('Auth:login_page') 
            
            user = authenticate(email=email, password=password)
            if user is None:
                messages.info(request, "Invalid username or Password.")
                return redirect('Auth:login_page')
            
            login(request,user)
            return redirect('Auth:index')
        
        except Exception as e:
            print(e)    
            
    
    return render(request,'login_page.html')