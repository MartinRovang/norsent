$(document).ready(function() {

$('.updateButton').on('click', function()){

    var member_id = $(this).attr('member_id');
    
    var name = $('#nameInput' +member_id).val();


    req = $.ajax({
        url: '/update',
        type: 'POST',
        data : {name:[name]}
    });

    $('memberSection')
}


}