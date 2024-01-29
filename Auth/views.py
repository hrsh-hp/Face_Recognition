from django.http import JsonResponse,HttpResponse
from django.shortcuts import render,redirect
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth import get_user_model
import uuid
from .helpers import send_email_token
from django.contrib import messages

User = get_user_model()

#for face recogniton
import face_recognition
import base64
import cv2
from PIL import Image
import numpy as np
from io import BytesIO

# Face Recognition view 
@csrf_exempt
def recognize_face(request):
    # print(known_faces)
    if request.method == "POST":
        try:
            # decoding the base64 received from frontend into image
            image_data = request.POST.get('imageData')
            img_data = base64.b64decode(image_data.split(',')[1])
            image = Image.open(BytesIO(img_data))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # getting face encodings from received image
            rec_face_locations = face_recognition.face_locations(frame, number_of_times_to_upsample=2)
            rec_face_encodings = face_recognition.face_encodings(frame,rec_face_locations)
         
            recognized_name = []
            name = "Unknown!!"

            #comparing known face encodings with received face encodings
            for rec_face_encoding in rec_face_encodings:
                
                #Getting the known faces from database
                known_faces = {}
                for face_obj in KnownFace.objects.all():
                    known_image_data = base64.b64decode(face_obj.image.split(',')[1])
                    known_image = Image.open(BytesIO(known_image_data))
                    known_faces[face_obj.name] = face_recognition.face_encodings(np.array(known_image))[0]
            

                matches = face_recognition.compare_faces(list(known_faces.values()), rec_face_encoding)
                
                if True in matches:
  
                    first_match_index = matches.index(True)
                    name = list(known_faces.keys())[first_match_index]
                    print(f"Welcome {name}")
                    recognized_name.append(name)
                    
                else :
                    print('face not matches')
                    
            print(recognized_name)
            # Convert a frame in to Jpeg
            _ , jpeg = cv2.imencode('.jpeg', frame)
            res_img = jpeg.tobytes()  
            response = base64.b64encode(res_img).decode('utf-8') 
            return JsonResponse({'name':name,'image':response})
                    
        except Exception as e:
            print(e)
            return JsonResponse({'err':str(e)})
        
    else:
        print('not a Post method')
        return JsonResponse({'err':"Invalid request method it must be POST"})

def index(request):
    return render(request, 'Auth/index.html')

#Register Page logic
def register(request):
    #When user request for registraion
    if request.method == "POST":
        try:
            email = request.POST.get('email')
            phone_num = request.POST.get('phone_num')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            user_image = request.POST.get('user_image')
            email_token = str(uuid.uuid4())
            user = User.objects.create(
                email= email,
                phone_num= phone_num,
                first_name = first_name,
                last_name = last_name,
                user_image = user_image,
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
    return render(request, 'Auth/register.html')

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
            
    
    return render(request,'Auth/login_page.html')