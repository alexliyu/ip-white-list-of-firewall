function change_option(number,index){
 for (var i = 1; i <= number; i++) {
      document.getElementById('current' + i).className = '';
      document.getElementById('content' + i).style.display = 'none';
 }
  document.getElementById('current' + index).className = 'on';
  document.getElementById('content' + index).style.display = 'block';
}
function ftab(num){
	for(var id = 0;id<=7;id++)
	{
		if(id==num)
		{
			document.getElementById("subnav"+id).style.display="block";
			document.getElementById("nav"+id).className="nav_on";
		}
		else
		{
			document.getElementById("subnav"+id).style.display="none";
			document.getElementById("nav"+id).className="";
		}
	}
}
