import time
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from .models import *
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .documents import RecipeDocument
from elasticsearch_dsl.query import MultiMatch
# Create your views here.

CACHE_TTL=getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

@login_required(login_url='/login/')
def recipe_page(request):
    # Fetching data inputted on frontend(form) to the backend
    if request.method == "POST":
     data=request.POST
     recipe_name=data.get('recipe_name')
     recipe_description=data.get('recipe_description')
     recipe_image=request.FILES['recipe_image']
    #  Or, recipe_image=request.FILES.get('recipe_image')

    # Now to store the fetched data to the database,
     Recipe.objects.create(
        recipe_name=recipe_name,
        recipe_description=recipe_description,
        recipe_image=recipe_image,
     )

     return redirect("/recipes/")

    queryset= Recipe.objects.all()

    if request.GET.get('search'):
      search_content=request.GET.get('search')
    
      if cache.get(search_content):
          print("Data from Cache")
          queryset=cache.get(search_content)

      else:    
         print("Data from Database")
         queryset=queryset.filter(recipe_name__icontains=search_content)  #Implementing Normal Search based on recipe name only.
         # # queryset=RecipeDocument.search().query('match', recipe_name=search_content)  #Implementing Elastic Search based on recipe name only.
         # query=MultiMatch(query=search_content, fields=['recipe_name', 'recipe_description'])
         # queryset=RecipeDocument.search().query(query)  #Implementing Elastic search based on Recipe name and description.
         cache.set(search_content, queryset)  #This 'search_content' and it's equivalent 'queryset' is now stored in cache side by side as a key value pair.

    context={'recipes': queryset}

    return render(request, 'recipes.html', context)

def update_recipe(request, id):
   queryset=Recipe.objects.get(id = id)
   if request.method == "POST":
     data=request.POST
     recipe_name=data.get('recipe_name')
     recipe_description=data.get('recipe_description')
     recipe_image=request.FILES.get('recipe_image')

     queryset.recipe_name=recipe_name
     queryset.recipe_description=recipe_description

     if recipe_image:
        queryset.recipe_image=recipe_image

     queryset.save()  
     return redirect("/recipes/")

   context={'recipe': queryset}
   return render(request, 'update_recipes.html', context)


   


def delete_recipe(request, id):
   queryset=Recipe.objects.get(id = id)
   queryset.delete()
   return redirect("/recipes/")

def login_page(request):
   if request.method == "POST":
      user_name=request.POST.get("username")
      password=request.POST.get("password")

      if User.objects.filter(username=user_name).exists():
         user=authenticate(username=user_name, password=password)

         if user is None:
            messages.error(request, 'Invalid Password')

         else:
            login(request, user=user) 
            return redirect('/recipes/')  

            

      else:
         messages.error(request, 'Invalid Username')
         redirect('/login/')

   return render(request, "login_page.html")

def logout_page(request):
   logout(request)
   return redirect('/login/')

@csrf_exempt
def register_page(request):
   if request.method == "POST":
      first_name=request.POST.get("firstname")
      last_name=request.POST.get("lastname")
      user_name=request.POST.get("username")
      password=request.POST.get("password")

      user=User.objects.filter(username=user_name)
      if user.exists():
         messages.info(request, 'Username already taken')
         redirect("/register/")

      else:
         user=User.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=user_name,
         )

         user.set_password(password)
         user.save()
         messages.info(request, 'Account created successfully!')
         # time.sleep(10)
         return redirect("/register/")


   return render(request, "register_page.html")
   