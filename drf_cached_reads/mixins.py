from rest_framework.generics import get_object_or_404 as _get_object_or_404

from .models import CachedQueryset


def get_object_or_404(queryset, *filter_args, **filter_kwargs):
    """
    Same as Django's standard shortcut, but make sure to raise 404
    if the filter_kwargs don't match the required types.
    """
    if isinstance(queryset, CachedQueryset):
        return queryset.get(*filter_args, **filter_kwargs)
    else:
        return _get_object_or_404(queryset, *filter_args, **filter_kwargs)


class CachedViewMixin(object):
    cache_version = 'default'

    def get_queryset(self):
        '''Get the queryset for the action

        If action is read action, return a CachedQueryset
        Otherwise, return a Django queryset
        '''
        queryset = super(CachedViewMixin, self).get_queryset()
        if self.action in ('list', 'retrieve'):
            return CachedQueryset(self.get_queryset_cache(), queryset=queryset)
        else:
            return queryset

    def get_queryset_cache(self):
        '''Get the cache to use for querysets

        Users should subclass cache.Cache and override this function to return
        an instance of the class.
        '''
        return self.cache_class()

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.

        Same as rest_framework.generics.GenericAPIView, but:
        - Failed assertions instead of deprecations
        """
        # Determine the base queryset to use.
        assert queryset is None, "Passing a queryset is disabled"
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup = self.kwargs.get(lookup_url_kwarg, None)
        assert lookup is not None, "Other lookup methods are disabled"
        filter_kwargs = {self.lookup_field: lookup}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj