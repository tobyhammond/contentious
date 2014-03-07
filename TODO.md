## Core

* Add CSS for:
  * Making the modal form look nice.


## Nice to haves

* Remove some of the `optionals` stuff on the client side.  Now that we have server-side validation with the errors passed through to the JS there's no need for the optionals stuff, apart from to have *required markers on the form fields.
* Add a hash of the editable items into a data-x attribute on the HTML tag when in edit mode.  This should then be submitted as a hidden input with the edit form and re-checked server side against the list of POST data keys.  If there are items in the POST data which are not allowed to be edited then the hashes won't match.  We could make this an optional check.
* Make the {% editable %} tag not require a closing tag if it's a self-closing HTML tag.

