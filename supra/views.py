from django.views.generic import ListView
from django.views.generic.edit import FormView
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import inlineformset_factory, modelformset_factory
from django.http import HttpResponse
from django.db.models import Q, F
import models
import json

"""
	@name: SuperListView
	@author: exile.sas
	@date: 13/10/2015
	@licence: creative commons
"""
class SupraListView(ListView):
	list_display = None
	search_fields = []

	def dispatch(self, request, *args, **kwargs):
		for field in self.search_fields:
			q = request.GET.get(field, False)
			if q:
				self.kwargs[field] = q
			#end if
		#end for
		return super(SupraListView, self).dispatch(request)
	#end def

	def get_queryset(self):
		queryset = super(SupraListView, self).get_queryset()
		q = Q()
		for column in self.search_fields:
			if column in self.kwargs:
				search = self.kwargs[column]
				kwargs = {
					'{0}__{1}'.format(column, 'icontains'): search, 
				}
				q = Q(q & Q(**kwargs))
			#end if
			queryset = queryset.filter(q)
		#end for
		return queryset
	#end def

	def get_context_data(self, **kwargs):
		context = super(SupraListView, self).get_context_data(**kwargs)
		context['num_rows'] = context['object_list'].count()
		context['object_list'] = context['object_list']
		return context
	#end def

	def render_to_response(self, context, **response_kwargs):
		json_dict = {}

		queryset = context["object_list"]
		if self.list_display:
			renderers = dict((key, F(value)) for key, value in self.Renderer.__dict__.iteritems() if not callable(value) and not key.startswith('__'))
			queryset = queryset.annotate(**renderers)
			queryset = queryset.values(*self.list_display)
			object_list = list(queryset)
		else:
			object_list = list(queryset.values())
		#end if

		page_obj = context["page_obj"]
		paginator = context["paginator"]
		num_rows = context["num_rows"]
		if page_obj:
			if page_obj.has_previous():
				json_dict["previous"] = page_obj.previous_page_number()
			#end if
			if page_obj.has_next():
				json_dict["next"] = page_obj.next_page_number()
			#endif
		#end if
		if paginator:
			json_dict["count"] = paginator.count
			json_dict["num_pages"] = paginator.num_pages
			json_dict["page_range"] = paginator.page_range
		#end if
		json_dict["num_rows"] = num_rows
		json_dict["object_list"] = object_list
		return HttpResponse(json.dumps(json_dict, cls=DjangoJSONEncoder), content_type="application/json")
	#end def

#end class

class SupraFormView(FormView):
	template_name = "supra/form.html"
	inlines = []
	validated_inilines = []
	invalided_inilines = []

	def form_valid(self, form):
		instance = form.save()
		for inline in self.validated_inilines:
			inline.instance = instance
			inline.save()
		#end for
		return HttpResponse(status=200)
	#end def

	def get_context_data(self, **kwargs):
		context = super(SupraFormView, self).get_context_data(**kwargs)
		context['inlines'] = []
		for inline in self.inlines:
			form_class = inline().get_form_class()
			context['inlines'].append(form_class())
		#end for
		return context
	#end def

	def post(self, request, *args, **kwargs):
		form_class = self.get_form_class()
		form = self.get_form(form_class)
		is_valid_form = form.is_valid()
		is_valid_inlines = self.is_valid_inlines()
		if is_valid_form and is_valid_inlines:
			return self.form_valid(form)
		#end if
		return self.form_invalid(form)
	#end def

	def is_valid_inlines(self):
		for inline in self.inlines:
			i = inline()
			form_class = i.get_form_class()
			form = form_class(**self.get_form_kwargs())
			if not form.is_valid():
				self.invalided_inilines.append(form)
			#end if
			self.validated_inilines.append(form)
		#end for
		if len(self.invalided_inilines) > 0:
			return False
		#end if
		return True
	#end for

	def form_invalid(self, form):
		errors = dict(form.errors)
		for i in self.invalided_inilines:
			errors['inlines'] = list(i.errors)
		#end for
		return HttpResponse(json.dumps(errors), status=400, content_type="application/json")
	#end def

#end class

class SupraInlineFormView(SupraFormView):
	base_model = None
	inline_model = None
	formset_class = None
	form_class = None
	
	def get_form_class(self):
		if self.formset_class and self.form_class:
			return inlineformset_factory(self.base_model, self.inline_model, form=self.form_class, formset=self.formset_class, exclude=[], extra=2)
		else:
			return inlineformset_factory(self.base_model, self.inline_model, exclude=[])
		#end if
	#end def
#end class