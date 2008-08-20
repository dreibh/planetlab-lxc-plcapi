# each module to define in "methods" the set of methods that it defines

#__all__ = """
#Accessors_standard
#Accessors_site
#""".split()

# this trick to support for site-local stuff does not work as it would be required at build-time - need to find something else 
# see also the specfile
__all__ = """
Accessors_standard
""".split()
