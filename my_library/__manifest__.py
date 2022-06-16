{
    
    'name': "My Library",  # Module title
    'summary': "Manage books easily",  # Module subtitle phrase
    'description': """
Manage Library
==============
Description related to library.
    """,  
    'author': "Jordan",
    'website': "http://www.example.com",
    'category': 'Tools',
    'version': '14.0.1',
    'depends': ['base'],

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/library_book.xml',
        'views/library_res_partner.xml',
        'views/library_book_categ.xml',
        'views/library_book_rent.xml',
        'wizard/library_book_rent_wizard.xml',
        'wizard/library_book_return_wizard.xml',
        'views/library_book_rating.xml',
        'wizard/book_review_wizard.xml'
    ],
}
