/* Author: 
Farsheed Ashouri
mail: farsheed.ashouri@gmail.com
*/
function showCenter(point)
{
var div = document.createElement("div");
div.style.background = "#dedede";
div.style.position = "absolute";
div.style.top = point.y + "px";
div.style.left = point.x + "px";
div.style.width = "100px";
div.style.height = "100px";
document.body.appendChild(div);
}

//<![CDATA[
        $(document).ready(function(){
        //================ uploading ==================


        //========================================

        $('a[rel*=light]').live('mouseover', function(){
            var lbl_id    = $(this).attr('id');
            if ( $('#lbc_' + lbl_id).length == 0 ){
                $(this).append('<div style="display:none;" rel="lbc" id=' + '"lbc_' + lbl_id + '"><img height="32" width="32" src="../static/images/jKEcVPZFk-2.gif"/></div>');
            }
        });
        $('a[rel*=light]').live('click', function(e) {
            //getting variables
            var lbl_id    = $(this).attr('id');
            var lbl_title = $(this).attr('title');
            var lbl_link  = $(this).attr('href');
            var lbl_vars  = $(this).attr('vars');
            $('#'+lbl_id).show(); //show the loading bar ...
            //calling ajax
            //showing lightbox_me
            //$('#lbc_' + lbl_id).show();
            //$('#lbc_' + lbl_id).lightbox_me();
            $('#lbc_' + lbl_id).lightbox_me({
                centered: true,
                overlayCSS: {background: 'black',opacity: .6},
                destroyOnClose: true,
                onLoad: function() { 
                    //$('#sign_up').find('input:first').focus()
                    }
                });
            ajax( lbl_link + '?' + lbl_vars +'&_t=' + lbl_title, [''],'lbc_' + lbl_id);
            e.preventDefault();
            $('#container').css('-webkit-filter', 'grayscale(100%)');
        });
            $('*[rel*=confirmation]').live('click',function(){
                $(document).find('div[rel*=lbc]').fadeOut(500);
                setTimeout("$(document).find('div[rel*=lbc]').trigger('close')", 600);
                //setTimeout("$(document).find('div[rel*=lbc]').remove()", 620);
                setTimeout("window.location.reload();", 650);
                //alert(al);
            });
            $('.close_light, *[rel*=close]').live('click',function(){
                $(document).find('div[rel*=lbc]').fadeOut(500);
                setTimeout("$(document).find('div[rel*=lbc]').trigger('close');",600);
                setTimeout("$(document).find('div[rel*=lbc]').remove();",620);
                $('#container').css('-webkit-filter', 'grayscale(0%)');
                //alert(al);
            });
        // Main Search:
        $('#hide_left_col').live('click', function(){
            var bh = $(this).html();
            
            if (bh=='•'){
            $('#leftCol').css('width','0px');
            $('#leftCol').toggle();
            setTimeout("$('#contentCol').css('margin-left', '0px');",100);
            $('body').removeClass('hasLeftCol');
            $('#contentCol').css('border-left', '1px solid #ccc');
            $('#contentCol').css('border-right', '1px solid #ccc');
            $(this).html('••');
                }
            else{
                $('#leftCol').css('width','179px');
                $('#contentCol').css('margin-left', '181px');
                $('body').addClass('hasLeftCol');
                $(this).html('•');
                $('#contentCol').css('border-right', '0px solid #ccc');
                $('#leftCol').fadeIn(1500);
                ajax('../leftbar',[],'leftCol')
            }
        });
        $('.textInput').live('click', function(){
            $(this).css('border','1px solid #9EE1FF');
            $(this).css('-moz-box-shadow','0pt 1px 8pt #9EE1FF');
            $(this).css('-webkit-box-shadow','0pt 1px 8pt #9EE1FF');
            $(this).css('box-shadow','0pt 1px 8pt #9EE1FF');
            $(this).css('background','#FFFEE6');
            $(this).animate({
                width: '55%',
              }, 500, function() {
                // Animation complete.
              });
        });
        $('.textInput').live('blur', function(){
            $(this).css('border','1px solid #eee');
            $(this).css('-moz-box-shadow','0pt 0px 0pt #FFE662');
            $(this).css('-webkit-box-shadow','0pt 0px 0pt #FFE662');
            $(this).css('box-shadow','0pt 0px 0pt #FFE662');
            $(this).css('background','#fff');
            $(this).animate({
                width: '25%',
              }, 500, function() {
                // Animation complete.
              });
        });
        $('.textInput').live('focus', function(){
            $(this).trigger('click');
        });
        

	$('#redactor_content').redactor();


    $('#q').click(function(){
    if ($('#q').val() == 'Search')
    {
    $('#q').val('');
    }
    });
    $('#q').blur(function(){
    if ($('#q').val() == '')
    {
    $('#q').val('Search');
    }
    });
       
}); //end














