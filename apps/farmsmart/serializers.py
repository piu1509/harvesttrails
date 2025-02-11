from rest_framework import serializers
from apps.processor.models import *
from apps.processor2.models import *
from apps.growerpayments.models import EntryFeeds , GrowerPayments
from apps.growerpayments.models import NasdaqApiData
from datetime import timedelta ,datetime ,date 
from apps.warehouseManagement.models import *
from apps.contracts.models import *

class GrowerPaymentsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = GrowerPayments
        fields = ['payment_amount', 'payment_date','payment_type','payment_confirmation']

class BaleReportFarmFieldSerializer(serializers.ModelSerializer):
    delivery_date = serializers.DateField(source='dt_class',read_only=True)
    delivery_id = serializers.CharField(source='bale_id', read_only=True)
    grower_name = serializers.CharField(source='ob3',read_only=True)
    grower_pmt = serializers.SerializerMethodField()
    delivery_lbs = serializers.DecimalField(max_digits=10, decimal_places=0, source='net_wt')

    class Meta:
        model = BaleReportFarmField
        fields = ['delivery_date', 'delivery_id', 'grower_name','crop','field_name','delivery_lbs','level','delivery_value','total_price','payment_due_date','grower_pmt']

    def get_grower_pmt(self, obj):
    
        grower_payments = GrowerPayments.objects.filter(delivery_id=obj.bale_id)
        return GrowerPaymentsSerializer(grower_payments, many=True).data
    
    def get_crop(self,obj):
        crop = "COTTON"
        return (crop)
    
    def get_payment_due_date(self, instance):
        if instance.level is not None:
            if instance.dt_class :
                date_str = str(instance.dt_class).split("/")
                dd = int(date_str[1])
                mm = int(date_str[0])
                yy = int(date_str[2])
                if len(str(yy)) == 2 : 
                    yyyy = int("20{}".format(yy))
                else:
                    yyyy = yy
                # specific_date = datetime(yyyy, mm, dd)
                # new_date = specific_date + timedelta(60)
                new_date = (datetime(yyyy, mm, dd)) + timedelta(60)
                payment_due_date = new_date.strftime("%m/%d/%y")
                return payment_due_date
            else:
              return "N/A"
        else:
            return "N/A"

    def get_delivery_value(self, instance):

        if instance.dt_class :
            str_date = str(instance.dt_class )
            if '-' in str_date :
                try :
                    str_date = str_date.split('-')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = date(int(yyyy), int(mm), int(dd))
                except :
                    pass
            elif '/' in str_date :
                try :
                    str_date = str_date.split('/')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = date(int(yyyy), int(mm), int(dd))
                except :
                    pass
            else:
                finale_date = ''
        else:
            pass

        check_entry = EntryFeeds.objects.filter(grower_id = instance.ob2)
        if len(check_entry) == 0 :
            pass
        if len(check_entry) == 1 :
            var = EntryFeeds.objects.get(grower_id = instance.ob2)
        if len(check_entry) > 1 :
            check_entry_with_date = EntryFeeds.objects.filter(grower_id = instance.ob2,from_date__lte=finale_date,to_date__gte=finale_date)
            check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = instance.ob2,from_date__isnull=True,to_date__isnull=True)
            if check_entry_with_date.exists() :
                var = EntryFeeds.objects.get(id = [i.id for i in check_entry_with_date][0])
            elif check_entry_with_no_date.exists() :
                var = EntryFeeds.objects.get(id = [i.id for i in check_entry_with_no_date][0])
    
        cpb_lbs = var.contract_base_price
        if cpb_lbs :
            cpb_lbs = var.contract_base_price
        else:
            cpb_lbs = 0.0
        sp_lbs = var.sustainability_premium
        if sp_lbs :
            sp_lbs = var.sustainability_premium
        else:
            sp_lbs = 0.0
        if instance.level == 'Bronze' :
            qp_lbs = 0.00
        elif instance.level == "Silver":
            qp_lbs = 0.02
        elif instance.level == "Gold":
            qp_lbs = 0.04
        elif instance.level == "None":
            qp_lbs = 0.00
                                
        if instance.level is not None:
            total_price = float(cpb_lbs) + float(sp_lbs) + float(qp_lbs)
            delivered_value = float(instance.net_wt) * float(total_price)
            del_value= "{0:.4f}".format(delivered_value)
            return del_value
          
        else:
            delivered_value = 0.00
            return delivered_value 
            
    def get_total_price(self, instance):
        if instance.dt_class :
            str_date = str(instance.dt_class )
            if '-' in str_date :
                try :
                    str_date = str_date.split('-')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = date(int(yyyy), int(mm), int(dd))
                except :
                    pass
            elif '/' in str_date :
                try :
                    str_date = str_date.split('/')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = date(int(yyyy), int(mm), int(dd))
                except :
                    pass
            else:
                finale_date = ''
        else:
            pass

        check_entry = EntryFeeds.objects.filter(grower_id = instance.ob2)
        if len(check_entry) == 0 :
            pass
        if len(check_entry) == 1 :
            var = EntryFeeds.objects.get(grower_id = instance.ob2)
        if len(check_entry) > 1 :
            check_entry_with_date = EntryFeeds.objects.filter(grower_id = instance.ob2,from_date__lte=finale_date,to_date__gte=finale_date)
            check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = instance.ob2,from_date__isnull=True,to_date__isnull=True)
            if check_entry_with_date.exists() :
                var = EntryFeeds.objects.get(id = [i.id for i in check_entry_with_date][0])
            elif check_entry_with_no_date.exists() :
                var = EntryFeeds.objects.get(id = [i.id for i in check_entry_with_no_date][0])
    
        cpb_lbs = var.contract_base_price
        if cpb_lbs :
            cpb_lbs = var.contract_base_price
        else:
            cpb_lbs = 0.0
        sp_lbs = var.sustainability_premium
        if sp_lbs :
            sp_lbs = var.sustainability_premium
        else:
            sp_lbs = 0.0
        if instance.level == 'Bronze' :
            qp_lbs = 0.00
        elif instance.level == "Silver":
            qp_lbs = 0.02
        elif instance.level == "Gold":
            qp_lbs = 0.04
        elif instance.level == "None":
            qp_lbs = 0.00
                                
        if instance.level is not None:
            total_price = float(cpb_lbs) + float(sp_lbs) + float(qp_lbs)
            total_prc=  "{0:.5f}".format(total_price)
            return total_prc  
        else:
            total_price = 0.00
            return total_price

    crop = serializers.SerializerMethodField(method_name='get_crop')    
    payment_due_date = serializers.SerializerMethodField(method_name='get_payment_due_date')    
    delivery_value = serializers.SerializerMethodField(method_name='get_delivery_value')    
    total_price = serializers.SerializerMethodField(method_name='get_total_price')    

class GrowerShipmentSerializer(serializers.ModelSerializer):
   
    delivery_id = serializers.DateField(source='shipment_id',read_only=True)
    grower_pmt = serializers.SerializerMethodField()
    grower_name = serializers.CharField(source='grower.name',read_only=True) 
    field_name = serializers.CharField(source='field.name',read_only=True)
   
    class Meta:
        model = GrowerShipment
        fields = ['id','delivery_date','delivery_id', 'grower_name','crop', 'variety','field_name','level','delivery_lbs','total_price','delivery_value','payment_due_date','grower_pmt']
        
    def get_grower_pmt(self, obj):
        grower_payments = GrowerPayments.objects.filter(delivery_id=obj.shipment_id)
        return GrowerPaymentsSerializer(grower_payments, many=True).data
    
    def get_delivery_date(self, instance):
        if instance.approval_date is None:
            return instance.process_date.strftime("%m/%d/%y")
        else:
            return instance.approval_date.strftime("%m/%d/%y")

    def get_payment_due_date(self, instance):
        if instance.approval_date is None:
            new_date = instance.process_date + timedelta(60)
        else:
            new_date = instance.approval_date + timedelta(60)
        return new_date.strftime("%m/%d/%y")
    
    def get_delivery_lbs(self, instance):
        if instance.received_amount is not None:
            del_lbs = int(float(instance.received_amount))
            return del_lbs
        else:
            del_lbs = int(float(instance.total_amount))
            return del_lbs

    def get_class(self,obj):
        level = "-"
        return (level)
 
    def get_total_price(self, instance):       
        var = None
        if instance.approval_date is None:
            
            check_entry_with_date = EntryFeeds.objects.filter(grower_id = instance.grower_id,from_date__lte=instance.process_date,to_date__gte=instance.process_date)
            check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = instance.grower_id,from_date__isnull=True,to_date__isnull=True)

            if check_entry_with_date.exists() :
                var = EntryFeeds.objects.get(id=[i.id for i in check_entry_with_date][0])
            elif check_entry_with_no_date.exists() :
                var = EntryFeeds.objects.get(id = [i.id for i in check_entry_with_no_date][0])

        else:
            check_entry_with_date = EntryFeeds.objects.filter(grower_id = instance.grower_id,from_date__lte=instance.approval_date,to_date__gte=instance.approval_date)
            check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = instance.grower_id,from_date__isnull=True,to_date__isnull=True)
            if check_entry_with_date.exists() :
                var = EntryFeeds.objects.get(id=[i.id for i in check_entry_with_date][0])  
            elif check_entry_with_no_date.exists() :
                var = EntryFeeds.objects.get(id = [i.id for i in check_entry_with_no_date][0])

        if not var :
            return None
        if var.contracted_payment_option == 'Fixed Price' :
            cpb_lbs = var.contract_base_price
            sp_lbs = var.sustainability_premium
            total_price =  float(cpb_lbs) + float(sp_lbs)
            total_prc= "{0:.5f}".format(total_price)
            return total_prc
        elif var.contracted_payment_option == 'Acreage Release' :
            cpb_lbs = var.contract_base_price
            sp_lbs = var.sustainability_premium
            total_price = float(cpb_lbs) + float(sp_lbs)
            total_prc= "{0:.5f}".format(total_price)
            return total_prc
        else:
            calculation_date = instance.approval_date
            if NasdaqApiData.objects.filter(date_api=calculation_date).count() !=0 :
                total_price_init = NasdaqApiData.objects.get(date_api=calculation_date).close_value_api
            else:
                for l in range(1,10):
                    next_date = calculation_date - timedelta(l)
                    if NasdaqApiData.objects.filter(date_api=next_date).count() !=0 :
                        total_price_init = NasdaqApiData.objects.get(date_api=next_date).close_value_api
                        break
            total_price2 = float(total_price_init) / 100
            total_price = total_price2 + 0.04
            total_prc= "{0:.5f}".format(total_price)
            return total_prc
        
    def get_delivery_value(self, instance):
        var = None 
        if instance.approval_date is None:
            check_entry_with_date = EntryFeeds.objects.filter(grower_id = instance.grower_id,from_date__lte=instance.process_date,to_date__gte=instance.process_date)
            check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = instance.grower_id,from_date__isnull=True,to_date__isnull=True)
            if check_entry_with_date.exists() :
                var = EntryFeeds.objects.get(id=[i.id for i in check_entry_with_date][0])
            elif check_entry_with_no_date.exists() :
                var = EntryFeeds.objects.get(id = [i.id for i in check_entry_with_no_date][0])
        else:
            check_entry_with_date = EntryFeeds.objects.filter(grower_id = instance.grower_id,from_date__lte=instance.approval_date,to_date__gte=instance.approval_date)
            check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = instance.grower_id,from_date__isnull=True,to_date__isnull=True)
            if check_entry_with_date.exists() :
                var = EntryFeeds.objects.get(id=[i.id for i in check_entry_with_date][0])  
            elif check_entry_with_no_date.exists() :
                var = EntryFeeds.objects.get(id = [i.id for i in check_entry_with_no_date][0])
        if not var :
            return None
        if var.contracted_payment_option == 'Fixed Price' :
            cpb_lbs = var.contract_base_price
            sp_lbs = var.sustainability_premium
            total_price =  float(cpb_lbs) + float(sp_lbs)
    
        elif var.contracted_payment_option == 'Acreage Release' :
            cpb_lbs = var.contract_base_price
            sp_lbs = var.sustainability_premium
            total_price = float(cpb_lbs) + float(sp_lbs)
            
        else:
            calculation_date = instance.approval_date
            if NasdaqApiData.objects.filter(date_api=calculation_date).count() !=0 :
                total_price_init = NasdaqApiData.objects.get(date_api=calculation_date).close_value_api
            else:
                for l in range(1,10):
                    next_date = calculation_date - timedelta(l)
                    if NasdaqApiData.objects.filter(date_api=next_date).count() !=0 :
                        total_price_init = NasdaqApiData.objects.get(date_api=next_date).close_value_api
                        break
            total_price2 = float(total_price_init) / 100
            total_price = total_price2 + 0.04
            
        if instance. received_amount is not None:
            del_lbs = int(float(instance.received_amount))
            delivered_value = float(del_lbs) * total_price
            del_value = "{0:.4f}".format(delivered_value)
            return del_value
        else:
            del_lbs = int(float(instance.total_amount))
            delivered_value = float(del_lbs) * total_price
            return delivered_value

    delivery_date = serializers.SerializerMethodField(method_name='get_delivery_date')
    payment_due_date = serializers.SerializerMethodField(method_name='get_payment_due_date')
    delivery_lbs = serializers.SerializerMethodField(method_name='get_delivery_lbs')
    level = serializers.SerializerMethodField(method_name='get_class')
    total_price = serializers.SerializerMethodField(method_name='get_total_price')
    delivery_value = serializers.SerializerMethodField(method_name='get_delivery_value')

class ShipmentManagementFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ['url', 'name', 'type']

    def get_url(self, obj):
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url

    def get_name(self, obj):
        return obj.file.name

    def get_type(self, obj):
        return obj.file.name.split('.')[-1]

class ShipmentManagementSerializer(serializers.ModelSerializer):
    files = ShipmentManagementFileSerializer(many=True)

    class Meta:
        model = ShipmentManagement
        fields = "__all__"
        
class ProcessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Processor
        fields = '__all__'  # This will include all the fields of the Processor model

class ProcessorUserSerializer(serializers.ModelSerializer):
    processor = ProcessorSerializer()

    class Meta:
        model = ProcessorUser
        fields = '__all__' 

class Processor2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Processor2
        fields = '__all__'  

class ProcessorUser2Serializer(serializers.ModelSerializer):
    processor2 = Processor2Serializer()

    class Meta:
        model = ProcessorUser2
        fields = '__all__' 


class CropDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CropDetails
        fields = [
            'id', 
            'crop', 
            'crop_type', 
            'contract_amount', 
            'amount_unit', 
            'per_unit_rate', 
            'left_amount',
        ]

class AdminProcessorContractDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminProcessorContractDocuments
        fields = [
            'id', 
            'name', 
            'document', 
            'document_status', 
            'uploaded_at',
        ]

class AdminProcessorContractSerializer(serializers.ModelSerializer):
    contractCrop = CropDetailsSerializer(many=True, read_only=True)  
    contractDocuments = AdminProcessorContractDocumentsSerializer(many=True, read_only=True)  

    class Meta:
        model = AdminProcessorContract
        fields = [
            'id', 
            'secret_key', 
            'processor_id', 
            'processor_type', 
            'processor_entity_name', 
            'contract_type', 
            'total_price', 
            'contract_start_date', 
            'contract_period', 
            'contract_period_choice', 
            'end_date', 
            'status', 
            'reason_for_rejection', 
            'created_at', 
            'updated_at', 
            'created_by', 
            'is_signed',
            'contractCrop',  
            'contractDocuments',
        ]
        read_only_fields = ['secret_key', 'created_at', 'updated_at', 'end_date']

    
class CustomerContractCropDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerContractCropDetails
        fields = [
            'id', 
            'crop', 
            'crop_type', 
            'contract_amount', 
            'amount_unit', 
            'per_unit_rate', 
            'left_amount',
        ]

class AdminCustomerContractDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminCustomerContractDocuments
        fields = [
            'id', 
            'name', 
            'document', 
            'document_status', 
            'uploaded_at',
        ]

class AdminCustomerContractSerializer(serializers.ModelSerializer):
    customerContractCrop = CustomerContractCropDetailsSerializer(many=True, read_only=True)  
    customerContractDocuments = AdminCustomerContractDocumentsSerializer(many=True, read_only=True)  

    class Meta:
        model = AdminCustomerContract
        fields = [
            'id', 
            'secret_key', 
            'customer_id',             
            'customer_name', 
            'contract_type', 
            'total_price', 
            'contract_start_date', 
            'contract_period', 
            'contract_period_choice', 
            'end_date', 
            'status', 
            'reason_for_rejection', 
            'created_at', 
            'updated_at', 
            'created_by', 
            'is_signed',
            'customerContractCrop',  
            'customerContractDocuments', 
        ]
        read_only_fields = ['secret_key', 'created_at', 'updated_at', 'end_date']


class ProcessorShipmentCropsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessorShipmentCrops
        fields = [
            'id',
            'crop_id',
            'crop',
            'crop_type',
            'ship_quantity',
            'ship_weight',
            'gross_weight',
            'net_weight',
            'weight_unit',
            'contract_weight_left',
            'payment_amount',
        ]


class ProcessorShipmentLotNumberTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessorShipmentLotNumberTracking
        fields = [
            'id',
            'additional_lot_number',
            'address',
            'description',
            'status',
        ]


class ProcessorWarehouseShipmentDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessorWarehouseShipmentDocuments
        fields = [
            'id',
            'document_name',
            'document_file',
            'uploaded_at',
        ]


class CarrierDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarrierDetails
        fields = [
            'id',
            'carrier_id',
            'description',
        ]


class ProcessorShipmentLogSerializer(serializers.ModelSerializer):
    updated_by = serializers.StringRelatedField()  

    class Meta:
        model = ProcessorShipmentLog
        fields = [
            'id',
            'description',
            'updated_at',
            'changes',
            'updated_by',
        ]


class ProcessorWarehouseShipmentSerializer(serializers.ModelSerializer):
    processor_shipment_crop = ProcessorShipmentCropsSerializer(many=True, read_only=True)
    shipment_carrier = CarrierDetailsSerializer(many=True, read_only=True)
    shipment_log = ProcessorShipmentLogSerializer(many=True, read_only=True)
    documents = ProcessorWarehouseShipmentDocumentsSerializer(many=True, source='processorwarehouseshipmentdocuments_set', read_only=True)
    additional_lot_numbers = ProcessorShipmentLotNumberTrackingSerializer(many=True, source='processorshipmentlotnumbertracking_set', read_only=True)

    class Meta:
        model = ProcessorWarehouseShipment
        fields = [
            'id',
            'shipment_id',
            'invoice_id',
            'contract',        
            'processor_id',
            'processor_type',
            'processor_entity_name',
            'processor_sku_list',
            'carrier_type',
            'outbound_type',
            'date_pulled',
            'purchase_order_name',
            'purchase_order_number',            
            'shipment_type',
            'border_receive_date',
            'border_leaving_date',
            'distributor_receive_date',
            'distributor_leaving_date',
            'border_back_receive_date',
            'border_back_leaving_date',
            'processor_receive_date',
            'status',
            'distributor_id',
            'distributor_entity_name',
            'customer_id',
            'customer_name',
            'warehouse_id',
            'warehouse_name',
            'warehouse_order_id',
            'product_payment_amount',
            'total_payment',
            'tax_amount',
            'is_paid',
            'invoice_approval',
            'approval_time',
            'updated_at',
            'customer_contract',
            'final_payment_date',
            'processor_shipment_crop',
            'shipment_carrier',
            'shipment_log',
            'documents',
            'additional_lot_numbers',
        ]


class WarehouseShipmentCropsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseShipmentCrops
        fields = [
            'id',
            'crop_id',
            'crop',
            'crop_type',
            'ship_quantity',
            'ship_weight',
            'gross_weight',
            'net_weight',
            'weight_unit',
            'contract_weight_left',
            'payment_amount',
        ]


class WarehouseShipmentLotNumberTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseShipmentLotNumberTracking
        fields = [
            'id',
            'additional_lot_number',
            'address',
            'description',
            'status',
        ]


class WarehouseCustomerShipmentDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseCustomerShipmentDocuments
        fields = [
            'id',
            'document_name',
            'document_file',
            'uploaded_at',
        ]


class CarrierDetails2Serializer(serializers.ModelSerializer):
    class Meta:
        model = CarrierDetails2
        fields = [
            'id',
            'carrier_id',
            'description',
        ]


class WarehouseShipmentLogSerializer(serializers.ModelSerializer):
    updated_by = serializers.StringRelatedField()  

    class Meta:
        model = WarehouseShipmentLog
        fields = [
            'id',
            'description',
            'updated_at',
            'changes',
            'updated_by',
        ]


class WarehouseCustomerShipmentSerializer(serializers.ModelSerializer):
    warehouse_shipment_crop = WarehouseShipmentCropsSerializer(many=True, read_only=True)
    customer_shipment_carrier = CarrierDetails2Serializer(many=True, read_only=True)
    shipmentLog = WarehouseShipmentLogSerializer(many=True, read_only=True)
    documents = WarehouseCustomerShipmentDocumentsSerializer(many=True, source='warehousecustomershipmentdocuments_set', read_only=True)
    additional_lot_numbers = WarehouseShipmentLotNumberTrackingSerializer(many=True, source='warehouseshipmentlotnumbertracking_set', read_only=True)

    class Meta:
        model = WarehouseCustomerShipment
        fields = [
            'id',
            'shipment_id',
            'invoice_id',
            'contract',  
            'warehouse_id',
            'warehouse_name',         
            'carrier_type',
            'outbound_type',
            'date_pulled',
            'purchase_order_name',
            'purchase_order_number',
            'shipment_type',
            'border_receive_date',
            'border_leaving_date',
            'customer_receive_date',
            'customer_leaving_date',
            'border_back_receive_date',
            'border_back_leaving_date',
            'warehouse_receive_date',
            'status',            
            'customer_id',
            'customer_name',              
            'product_payment_amount',
            'total_payment',
            'tax_amount',
            'is_paid',
            'invoice_approval',
            'approval_time',
            'updated_at',           
            'final_payment_date',
            'warehouse_shipment_crop',
            'customer_shipment_carrier',
            'shipmentLog',
            'documents',
            'additional_lot_numbers',
        ]

