from django.http import JsonResponse
from django.shortcuts import render, redirect
from orders.models import Order
from accounts.models import GuestEmail
from .models import Cart
from addresses.models import Address
from products.models import Product
from accounts.forms import LoginForm, GuestForm
from billing.models import BillingProfile
from addresses.forms import AddressForm


def cart_detail_api_view(request):
	cart_obj,new_obj=Cart.objects.new_or_get(request)
	products=[{"id":prod.id,"url":prod.get_url(),"title":prod.title,"price":prod.price} for prod in cart_obj.products.all()]
	cart_data={"products":products,"total":cart_obj.total}
	return JsonResponse(cart_data)

def cart_home(request):
	cart_obj,new_obj=Cart.objects.new_or_get(request)
	return render(request,"carts/home.html",{"cart":cart_obj})


def cart_update(request):
	product_id=request.POST.get('product_id')
	if product_id is not None:
		try:
			product_obj=Product.objects.get(id=product_id)
		except Product.DoesNotExist:
			return redirect("cart:home")
		cart_obj,new_obj=Cart.objects.new_or_get(request)
		if product_obj in cart_obj.products.all():
			cart_obj.products.remove(product_obj)
			added=False
		else:
			cart_obj.products.add(product_obj)
			added=True
		request.session['cart_items']=cart_obj.products.count()

		if request.is_ajax():
			print("Ajax Request")
			json_data={
				"added":added,
				"removed":not added,
				"cartItemCount":cart_obj.products.count()
			}
			return JsonResponse(json_data)
	return redirect("cart:home")


def checkout_home(request):
	cart_obj , cart_created=Cart.objects.new_or_get(request)
	order_obj=None
	if cart_created or cart_obj.products.count()==0:
		return redirect("cart:home")

	login_form=LoginForm()
	guest_form=GuestForm()
	address_form=AddressForm()
	billing_address_id=request.session.get("billing_address_id", None)
	shipping_address_id=request.session.get("shipping_address_id",None)

	billing_profile , billing_profile_created=BillingProfile.objects.new_or_get(request)
	if billing_profile is not None:
		order_obj, order_obj_created=Order.objects.new_or_get(billing_profile,cart_obj)
		if shipping_address_id:
			order_obj.shipping_address=Address.objects.get(id=shipping_address_id)
			del request.session["shipping_address_id"]
		if billing_address_id:
			order_obj.billing_address=Address.objects.get(id=billing_address_id)
			del request.session["billing_address_id"]
		if shipping_address_id or billing_address_id:
			order_obj.save()

	if request.method=="POST":
		is_done=order_obj.check_done()
		if is_done:
			order_obj.mark_paid()
			request.session['cart_items']=0
			del request.session['cart_id']
			return redirect("cart:success")
			
	context={
		"order_object":order_obj,
		"billing_profile":billing_profile,
		"login_form":login_form,
		"guest_form":guest_form,
		"address_form":address_form,
	}
	return render(request,"carts/checkout.html",context)


def checkout_done_view(request):
	return render(request,"carts/checkout-done.html",{})
