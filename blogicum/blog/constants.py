from django.utils import timezone

NUMBER_OF_POSTS = 10

FILTERS_FOR_PUBLIC = {
    'is_published': True,
    'category__is_published': True,
    'pub_date__lte': timezone.now()
}
